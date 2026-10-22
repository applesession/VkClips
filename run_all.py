#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import time
import os
import threading
import datetime
from pathlib import Path

# ---------- ФИКС КОДИРОВКИ ДЛЯ WINDOWS ----------
os.environ["PYTHONIOENCODING"] = "utf-8"

ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
LOG_FILE = ROOT_DIR / "logs" / "orchestrator.log"
UPDATE_FILE = ROOT_DIR / "data" / "last_update.txt"

UPDATE_INTERVAL = 86400
RESTART_DELAY = 5

# ДОБАВЛЕНО ДЛЯ CLEANER
CLEANER_INTERVAL = 86400  # 24 часа


import logging
from logging.handlers import TimedRotatingFileHandler

# --- notifier (patch.py) ---
try:
    from core.notifier import alert_error, alert_warn, alert_info, alert_ok
except Exception:
    def alert_error(_msg): pass
    def alert_warn(_msg): pass
    def alert_info(_msg): pass
    def alert_ok(_msg): pass

_orch_logger = None


def _get_orch_logger():
    global _orch_logger
    if _orch_logger is None:
        _orch_logger = logging.getLogger("orchestrator")
        _orch_logger.setLevel(logging.INFO)
        _orch_logger.propagate = False
        if not _orch_logger.handlers:
            try:
                LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            fh = TimedRotatingFileHandler(
                LOG_FILE, when="midnight", backupCount=14, encoding="utf-8"
            )
            fh.setFormatter(logging.Formatter(
                "[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            ))
            _orch_logger.addHandler(fh)
    return _orch_logger


def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        _get_orch_logger().info(msg)
    except Exception as e:
        print(f"[orchestrator] log() error: {e}")


def need_update():
    if not UPDATE_FILE.exists():
        return True
    try:
        with open(UPDATE_FILE, "r", encoding="utf-8") as f:
            last = datetime.datetime.fromisoformat(f.read().strip())
        return (datetime.datetime.now() - last).total_seconds() > UPDATE_INTERVAL
    except:
        return True


def update_ytdlp():
    if not need_update():
        return
    log("Updating yt-dlp...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        with open(UPDATE_FILE, "w", encoding="utf-8") as f:
            f.write(datetime.datetime.now().isoformat())
        log("yt-dlp updated")
    except Exception as e:
        log(f"Failed to update yt-dlp: {e}")


def run_script(name, script_path):
    log(f"Starting {name}...")
    # ВАЖНО: Возвращаем sys.executable (путь к питону текущего venv), убираем prlimit и nice
    return subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,
        cwd=str(ROOT_DIR),
    )


def monitor_process(name, process, stop_event):
    for line in process.stdout:
        if stop_event.is_set():
            break
        log(f"[{name}] {line.strip()}")


# ДОБАВЛЕНО ДЛЯ CLEANER – функция запуска cleaner'а и stats
def run_cleaner_sync():
    log("Scheduled cleaner started")
    try:
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "vk_cleaner.py")],
            cwd=str(ROOT_DIR),
            check=True,
        )
        log("Scheduled cleaner finished successfully")
    except subprocess.CalledProcessError as e:
        log(f"Scheduled cleaner failed with exit code {e.returncode}")
    except Exception as e:
        log(f"Scheduled cleaner error: {e}")

    log("Scheduled stats collector started")
    try:
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "stats_collector.py")],
            cwd=str(ROOT_DIR),
            check=True,
        )
        log("Scheduled stats collector finished successfully")
    except subprocess.CalledProcessError as e:
        log(f"Scheduled stats collector failed with exit code {e.returncode}")
    except Exception as e:
        log(f"Scheduled stats collector error: {e}")


def ensure_vk_token() -> bool:
    """Проверяет, что постоянный токен задан до запуска процессов."""
    from config.config import VK_ACCESS_TOKEN

    if VK_ACCESS_TOKEN.strip():
        log("[vk_token] VK_ACCESS_TOKEN задан")
        return True
    log("[vk_token] VK_ACCESS_TOKEN отсутствует в окружении или .env")
    return False


def main():
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"WARNING: Could not create log dir: {e}")

    UPDATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    log("=" * 60)
    log("ORCHESTRATOR STARTED")
    alert_ok("Оркестратор запущен")
    log("=" * 60)

    update_ytdlp()
    if not ensure_vk_token():
        log("Не удалось подготовить VK-токен. Выход.")
        log("Задай постоянный VK_ACCESS_TOKEN в .env или окружении")
        sys.exit(1)

    processes = {}
    stop_events = {}
    threads = {}

    def start_all():
        processes["populator"] = run_script("populator", SCRIPTS_DIR / "populator.py")
        stop_events["populator"] = threading.Event()
        threads["populator"] = threading.Thread(
            target=monitor_process,
            args=("populator", processes["populator"], stop_events["populator"]),
            daemon=True
        )
        threads["populator"].start()

        processes["loader"] = run_script("loader", SCRIPTS_DIR / "loader.py")
        stop_events["loader"] = threading.Event()
        threads["loader"] = threading.Thread(
            target=monitor_process,
            args=("loader", processes["loader"], stop_events["loader"]),
            daemon=True
        )
        threads["loader"].start()

        # --- vk_listener (patch.py) ---
        processes["vk_listener"] = run_script("vk_listener", SCRIPTS_DIR / "vk_listener.py")
        stop_events["vk_listener"] = threading.Event()
        threads["vk_listener"] = threading.Thread(
            target=monitor_process,
            args=("vk_listener", processes["vk_listener"], stop_events["vk_listener"]),
            daemon=True,
        )
        threads["vk_listener"].start()

    start_all()

    last_cleaner_run = time.time()

    try:
        last_update_check = time.time()
        while True:
            time.sleep(2)

            for name, proc in list(processes.items()):
                if proc.poll() is not None:
                    log(f"{name} died (exit code {proc.returncode}). Restarting in {RESTART_DELAY}s...")
                    alert_error(f"{name} упал (exit code {proc.returncode}). Перезапуск...")
                    stop_events[name].set()
                    time.sleep(RESTART_DELAY)
                    processes[name] = run_script(name, SCRIPTS_DIR / f"{name}.py")
                    stop_events[name] = threading.Event()
                    threads[name] = threading.Thread(
                        target=monitor_process,
                        args=(name, processes[name], stop_events[name]),
                        daemon=True
                    )
                    threads[name].start()

            if time.time() - last_update_check > UPDATE_INTERVAL:
                update_ytdlp()
                last_update_check = time.time()

            if time.time() - last_cleaner_run >= CLEANER_INTERVAL:
                log("Triggering scheduled cleaner...")
                last_cleaner_run = time.time()
                cleaner_thread = threading.Thread(target=run_cleaner_sync, daemon=True)
                cleaner_thread.start()

    except KeyboardInterrupt:
        log("Stopping orchestrator...")
        for name, proc in processes.items():
            log(f"Terminating {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        log("All processes stopped")
        alert_warn("Оркестратор остановлен вручную")
        sys.exit(0)


if __name__ == "__main__":
    main()
