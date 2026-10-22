"""
Busy-флаг загрузчика для отображения состояния в vk_listener.
Файл-лок: есть файл → основа занята.
"""
import time
from pathlib import Path

from config.config import DATA_DIR

BUSY_FILE = DATA_DIR / "loader_busy.lock"
STALE_SECONDS = 600  # если файл старше 10 минут — считаем устаревшим


def set_busy() -> None:
    BUSY_FILE.parent.mkdir(parents=True, exist_ok=True)
    BUSY_FILE.write_text(str(int(time.time())), encoding="utf-8")


def clear_busy() -> None:
    try:
        BUSY_FILE.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass


def is_busy() -> bool:
    if not BUSY_FILE.exists():
        return False
    try:
        ts = int(BUSY_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return False
    if time.time() - ts > STALE_SECONDS:
        # Устаревший лок (упал процесс) — снимаем
        clear_busy()
        return False
    return True
