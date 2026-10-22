#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from config.config import VK_GROUP_ID, DAILY_LIMIT_DEFAULT
from core.db import add_group, init_dbs

def main():
    init_dbs()

    name = "Подними Настроение"
    if not VK_GROUP_ID.isdigit() or int(VK_GROUP_ID) == 0:
        print("❌ Укажи числовой VK_GROUP_ID в .env")
        return
    group_id = -int(VK_GROUP_ID)

    add_group(name, group_id, DAILY_LIMIT_DEFAULT)
    print(f"✅ Группа '{name}' (ID: {group_id}) добавлена в БД.")

if __name__ == "__main__":
    main()
