import argparse
import asyncio
from typing import List, Tuple

from tortoise import Tortoise

from app.settings.config import settings


def fmt_cols(cols: List[str]) -> str:
    return ", ".join(f"`{c}`" for c in cols)


async def get_columns(conn, db: str, table: str) -> List[Tuple[str, str, str, str, str]]:
    sql = (
        "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, COLUMN_TYPE, IS_NULLABLE "
        "FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ORDINAL_POSITION"
    )
    rows = await conn.execute_query(sql, [db, table])
    # rows: (columns, data)
    data = rows[1]
    # Normalize to list of dicts
    norm = []
    for r in data:
        if isinstance(r, dict):
            norm.append(r)
        else:
            # tuple order matches SELECT
            norm.append(
                {
                    "COLUMN_NAME": r[0],
                    "DATA_TYPE": r[1],
                    "CHARACTER_MAXIMUM_LENGTH": r[2],
                    "COLUMN_TYPE": r[3],
                    "IS_NULLABLE": r[4],
                }
            )
    return norm


async def migrate(src_db: str, dst_db: str, table: str, upsert_key: str, preserve_id: bool) -> None:
    # init ORM
    await Tortoise.init(settings.TORTOISE_ORM)
    alias = settings.TORTOISE_ORM["apps"]["models"]["default_connection"]
    conn = Tortoise.get_connection(alias)

    # compare columns
    src_cols = await get_columns(conn, src_db, table)
    dst_cols = await get_columns(conn, dst_db, table)

    src_colnames = [r["COLUMN_NAME"] for r in src_cols]
    dst_colnames = [r["COLUMN_NAME"] for r in dst_cols]

    src_only = [c for c in src_colnames if c not in dst_colnames]
    dst_only = [c for c in dst_colnames if c not in src_colnames]

    common = [c for c in src_colnames if c in dst_colnames]

    if not preserve_id and "id" in common:
        common.remove("id")

    print("[migrate] table:", table)
    print("[migrate] src:", src_db, "dst:", dst_db)
    print("[migrate] src_only:", src_only)
    print("[migrate] dst_only:", dst_only)
    print("[migrate] common:", common)

    if not common:
        print("[migrate] No common columns to migrate. Abort.")
        return

    # build upsert SQL; avoid updating the upsert key itself
    update_cols = [c for c in common if c != upsert_key]

    # extra destination-only columns to satisfy NOT NULLs / defaults
    extra_dst_cols = []
    extra_src_vals = []
    if "secret" in dst_colnames and "secret" not in common:
        extra_dst_cols.append("secret")
        extra_src_vals.append("''")
    if "is_deleted" in dst_colnames and "is_deleted" not in common:
        extra_dst_cols.append("is_deleted")
        extra_src_vals.append("0")
    if "created_at" in dst_colnames and "created_at" not in common:
        extra_dst_cols.append("created_at")
        extra_src_vals.append("NOW()")
    if "updated_at" in dst_colnames and "updated_at" not in common:
        extra_dst_cols.append("updated_at")
        extra_src_vals.append("NOW()")

    insert_cols_sql = fmt_cols(common + extra_dst_cols)
    select_cols_sql = fmt_cols(common) + (", " + ", ".join(extra_src_vals) if extra_src_vals else "")
    update_sql = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in update_cols)

    sql_insert = (
        f"INSERT INTO `{dst_db}`.`{table}` ({insert_cols_sql}) "
        f"SELECT {select_cols_sql} FROM `{src_db}`.`{table}` "
        f"WHERE `{src_db}`.`{table}`.`{upsert_key}` IS NOT NULL AND `{src_db}`.`{table}`.`{upsert_key}`<>'' "
        f"ON DUPLICATE KEY UPDATE {update_sql};"
    )

    # execute insert/upsert
    await conn.execute_script(sql_insert)
    print("[migrate] upsert completed")

    # field mapping updates (conditional)
    updates = []
    # src desc/short_desc -> dst description
    if "description" in dst_colnames and ("desc" in src_colnames or "short_desc" in src_colnames):
        coalesce = []
        if "desc" in src_colnames:
            coalesce.append("s.`desc`")
        if "short_desc" in src_colnames:
            coalesce.append("s.`short_desc`")
        expr = "COALESCE(" + ", ".join(coalesce) + ")"
        updates.append(f"d.`description`={expr}")
    # src icon -> dst logo_url
    if "logo_url" in dst_colnames and "icon" in src_colnames:
        updates.append("d.`logo_url`=s.`icon`")
    # src qr_code_url -> dst qrcode_url
    if "qrcode_url" in dst_colnames and "qr_code_url" in src_colnames:
        updates.append("d.`qrcode_url`=s.`qr_code_url`")
    # timestamps
    if "created_at" in dst_colnames and "create_datetime" in src_colnames:
        updates.append("d.`created_at`=s.`create_datetime`")
    if "updated_at" in dst_colnames and "update_datetime" in src_colnames:
        updates.append("d.`updated_at`=s.`update_datetime`")
    # ensure is_deleted = 0
    if "is_deleted" in dst_colnames:
        updates.append("d.`is_deleted`=0")

    if updates:
        sql_update = (
            f"UPDATE `{dst_db}`.`{table}` d "
            f"JOIN `{src_db}`.`{table}` s ON d.`{upsert_key}`=s.`{upsert_key}` "
            f"SET " + ", ".join(updates) + ";"
        )
        await conn.execute_script(sql_update)
        print("[migrate] field mapping updates applied")

    print("[migrate] Done")


async def main():
    parser = argparse.ArgumentParser(description="Migrate MyWechat data between databases on same MySQL instance")
    parser.add_argument("--src", default="myweb_dev", help="Source database name")
    parser.add_argument("--dst", default="myweb_dev2", help="Destination database name")
    parser.add_argument("--table", default="MyWechat", help="Table name")
    parser.add_argument("--upsert-key", dest="upsert_key", default="appid", help="Unique key for upsert")
    parser.add_argument("--preserve-id", action="store_true", help="Preserve id values (may conflict)")
    args = parser.parse_args()

    await migrate(args.src, args.dst, args.table, args.upsert_key, args.preserve_id)


if __name__ == "__main__":
    asyncio.run(main())
