import asyncio
import os
import sys
from tortoise import Tortoise

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.settings.config import settings


async def has_table(conn, name: str) -> bool:
    try:
        await conn.execute_query(f"SELECT 1 FROM `{name}` LIMIT 1")
        print(f"TABLE_OK {name}")
        return True
    except Exception as e:
        print(f"TABLE_FAIL {name} {e}")
        return False


async def has_column(conn, table: str, col: str) -> bool:
    try:
        rows = await conn.execute_query_dict(f"SHOW COLUMNS FROM `{table}` LIKE '{col}'")
        ok = len(rows) > 0
        print(f"COLUMN_OK {table}.{col}" if ok else f"COLUMN_MISS {table}.{col}")
        return ok
    except Exception as e:
        print(f"COLUMN_FAIL {table}.{col} {e}")
        return False


async def main():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    conn = Tortoise.get_connection('mysql')

    ok = True
    # tables
    for t in ['MyWechat', 'Category', 'Banner', 'Favorite', 'Event', 'user', 'WxUser']:
        ok = await has_table(conn, t) and ok
    # columns on user
    ok = await has_column(conn, 'user', 'wx_openid') and ok
    ok = await has_column(conn, 'user', 'wx_unionid') and ok

    print('VERIFY_OK' if ok else 'VERIFY_FAIL')
    await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(main())
