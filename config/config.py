import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
TEMP_DIR = ROOT_DIR / "temp"
LOGS_DIR = ROOT_DIR / "logs"

DB_USED = DATA_DIR / "used_videos.db"
DB_QUEUE = DATA_DIR / "queue.db"
DB_GROUPS = DATA_DIR / "groups.db"

# ================== YouTube ==================
MAX_VIDEOS_PER_HASHTAG = 500
MIN_VIEWS = 3000
MAX_VIEWS = 300000
MIN_LIKES_RATIO = 0.01
MIN_DURATION = 5
MAX_DURATION = 165
MIN_MONTHS_AGO = 0
MAX_MONTHS_AGO = 12

# ================== Очередь ==================
TARGET_VIDEOS = 90
SLEEP_LOADER = 60

# ================== Постинг ==================
GROUP_COOLDOWN = 7200             # 2 часа между постами в одну группу
DAILY_LIMIT_DEFAULT = 1           # постов в день на группу
ACCOUNT_DAILY_LIMIT = 10          # постов в день на аккаунт
BLOCK_DAYS = 5                    # пауза после блокировки VK
LOADER_PAUSE_MIN = 600            # пауза после публикации, секунд
LOADER_PAUSE_MAX = 1600

# ================== Дополнительные настройки ==================
RETRY_COUNT = 1
SLEEP_BETWEEN_HASHTAGS = 10
BATCH_SIZE = 50

# ================== API ==================
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN", "").strip()
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN", "").strip()
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "").strip()
VK_ADMIN_ID = os.getenv("VK_ADMIN_ID", "").strip()
VK_ALERT_PEER_ID = os.getenv("VK_ALERT_PEER_ID", "").strip() or VK_ADMIN_ID
VK_API_VERSION = "5.131"
VK_CLIENT_ID = 6287487            # shortVideo.create
YT_API_KEY = os.getenv("YT_API_KEY", "").strip()
