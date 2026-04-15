#!/usr/bin/env python3
"""
scripts/reverse_geocode_addresses.py
─────────────────────────────────────
批量反向地理编码：为 buildings 表的每一行用 Nominatim 查询街道地址，
写回 buildings.address 列。

【运行前提条件】
  1. 先执行以下 SQL 添加列（脚本也会自动检测并添加）：
         ALTER TABLE buildings ADD COLUMN IF NOT EXISTS address TEXT;
  2. DB 连接必须有 UPDATE 权限（即管理员账户，不能用只读的 solarmap_api_ro）。

【用法】
  # 先安装依赖（只需一次）：
  pip install psycopg[binary] requests tqdm python-dotenv

  # 试跑前 100 条（建议先验证输出格式）：
  python scripts/reverse_geocode_addresses.py --limit 100

  # 全量跑（约 40 951 条，1 req/s，预计 11-12 小时）：
  python scripts/reverse_geocode_addresses.py

  # 查看进度（不查询 Nominatim，只打印剩余条数）：
  python scripts/reverse_geocode_addresses.py --dry-run

【恢复机制】
  脚本按 --batch-size 条为一批，每批写入 PG 后立即 COMMIT。
  中断后重跑时，会自动跳过 address IS NOT NULL 的行，
  因此最多损失 (--batch-size - 1) 条进度。

【Nominatim 使用条款】
  - 最大 1 req/s（--delay 默认 1.1s，留余量）
  - 必须带 User-Agent（已设置为 SolarMapAPI/1.0）
  - 仅供非商业用途；商业项目请换用 Mapbox / Google Geocoding API
  - 参考：https://operations.osmfoundation.org/policies/nominatim/
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

# ─── 路径处理：允许从仓库任意子目录运行 ───────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[1]  # Backend/api/
sys.path.insert(0, str(_REPO_ROOT))

# 加载 .env（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
except ImportError:
    pass  # python-dotenv 未安装时直接用环境变量

import psycopg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ─── 常量 ──────────────────────────────────────────────────────────────────
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
_UA_TEMPLATE = "SolarMapAPI/1.0 (3D Solar Potential Analysing; contact: {email})"
DEFAULT_DELAY = 1.1          # Nominatim ToS: ≤ 1 req/s
DEFAULT_BATCH_SIZE = 100     # 每批 COMMIT 一次
DEFAULT_LIMIT = 0            # 0 = 全量


# ─── Nominatim 调用 ─────────────────────────────────────────────────────────

def reverse_geocode(lat: float, lng: float, session: requests.Session) -> str | None:
    """
    调用 Nominatim，返回格式化的街道地址字符串，失败时返回 None。
    """
    try:
        resp = session.get(
            NOMINATIM_URL,
            params={"lat": lat, "lon": lng, "format": "json", "zoom": 18},
            timeout=15,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
    except Exception as exc:
        logger.warning("Nominatim request failed (lat=%.6f lng=%.6f): %s", lat, lng, exc)
        return None

    return _format_address(data)


def _format_address(data: dict[str, Any]) -> str | None:
    """
    从 Nominatim 响应中构建简洁地址：
        {门牌} {街道}, {郊区}, {州} {邮编}
    如果结构化组件不够，退回到 display_name 的前半部分。
    """
    addr = data.get("address", {})

    # 门牌 + 道路
    road = (addr.get("road")
            or addr.get("pedestrian")
            or addr.get("path")
            or addr.get("footway"))
    house = addr.get("house_number")

    parts: list[str] = []
    if road:
        parts.append(f"{house} {road}" if house else road)

    # 郊区 / 街区
    suburb = (addr.get("suburb")
              or addr.get("neighbourhood")
              or addr.get("city_district")
              or addr.get("quarter"))
    if suburb:
        parts.append(suburb)

    # 州 + 邮编
    state = addr.get("state")
    postcode = addr.get("postcode")
    if state and postcode:
        parts.append(f"{state} {postcode}")
    elif postcode:
        parts.append(postcode)

    if parts:
        return ", ".join(parts)

    # 退路：用 display_name，去掉 "Australia" 后缀
    display: str = data.get("display_name", "")
    if display:
        # 通常格式: "123 Collins St, Melbourne, Victoria 3000, Australia"
        if display.endswith(", Australia"):
            display = display[: -len(", Australia")]
        return display.strip()

    return None


# ─── 数据库操作 ─────────────────────────────────────────────────────────────

def _conninfo() -> str:
    required = {"DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"}
    missing = required - set(os.environ)
    if missing:
        sys.exit(
            f"[ERROR] 缺少环境变量: {', '.join(sorted(missing))}\n"
            "请先复制 .env.example 为 .env 并填写 DB_* 值（需要有 UPDATE 权限的账户）。"
        )
    return (
        f"host={os.environ['DB_HOST']} "
        f"port={os.environ.get('DB_PORT', 5432)} "
        f"dbname={os.environ['DB_NAME']} "
        f"user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASSWORD']}"
    )


def ensure_address_column(conn: psycopg.Connection) -> None:
    """
    确保 buildings.address 列存在。

    - 如果列已存在 → 直接跳过（支持重跑）
    - 如果列不存在且当前用户有权限 → 自动 ALTER TABLE 添加
    - 如果列不存在但当前用户无权限 → 打印需手动执行的 SQL，退出
    """
    # 先查列是否已存在，避免对无权限用户触发 ALTER
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name   = 'buildings'
              AND column_name  = 'address';
        """)
        already_exists = cur.fetchone() is not None

    if already_exists:
        logger.info("buildings.address 列已存在，跳过 ALTER TABLE。")
        return

    # 列不存在，尝试添加
    try:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE buildings ADD COLUMN address TEXT;")
        conn.commit()
        logger.info("buildings.address 列已创建。")
    except psycopg.errors.InsufficientPrivilege:
        conn.rollback()
        sys.exit(
            "\n[ERROR] 当前 DB 用户没有 ALTER TABLE 权限（需要表的 owner 或 superuser）。\n\n"
            "请让 DB 管理员（或用 superuser 账户）手动执行以下 SQL：\n\n"
            "    ALTER TABLE buildings ADD COLUMN IF NOT EXISTS address TEXT;\n\n"
            "执行完成后，再用原来的账户重新运行本脚本即可。\n"
        )


def count_remaining(conn: psycopg.Connection) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM buildings WHERE address IS NULL OR address = '';"
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0


def fetch_batch(
    conn: psycopg.Connection,
    batch_size: int,
    limit: int,
) -> list[tuple[int, float, float]]:
    """
    拉取下一批需要处理的行（address IS NULL），
    如果 limit > 0 则只返回 min(batch_size, limit) 条。
    """
    n = batch_size if limit == 0 else min(batch_size, limit)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT structure_id, lat, lng
            FROM buildings
            WHERE address IS NULL OR address = ''
            ORDER BY structure_id
            LIMIT %s;
            """,
            (n,),
        )
        return cur.fetchall()


def flush_batch(
    conn: psycopg.Connection,
    results: list[tuple[str | None, int]],
) -> None:
    """将 [(address, structure_id), ...] 批量写入 PG 并 COMMIT。"""
    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE buildings SET address = %s WHERE structure_id = %s;",
            results,
        )
    conn.commit()


# ─── 主流程 ─────────────────────────────────────────────────────────────────

def run(
    limit: int,
    batch_size: int,
    delay: float,
    dry_run: bool,
    email: str,
) -> None:
    conninfo = _conninfo()

    with psycopg.connect(conninfo) as conn:
        ensure_address_column(conn)
        remaining = count_remaining(conn)
        logger.info("待处理行数（address IS NULL）: %d", remaining)

        if dry_run:
            logger.info("--dry-run 模式，不发送任何请求。")
            return

        if remaining == 0:
            logger.info("所有建筑均已有地址，无需处理。")
            return

        total_done = 0
        effective_limit = min(limit, remaining) if limit > 0 else remaining

        session = requests.Session()
        session.headers["User-Agent"] = _UA_TEMPLATE.format(email=email)
        logger.info("User-Agent: %s", session.headers["User-Agent"])

        logger.info(
            "开始处理 %d 条（batch=%d, delay=%.1fs）……",
            effective_limit, batch_size, delay,
        )

        while True:
            rows = fetch_batch(conn, batch_size, effective_limit - total_done if limit > 0 else 0)
            if not rows:
                break

            batch_results: list[tuple[str | None, int]] = []
            for structure_id, lat, lng in rows:
                address = reverse_geocode(lat, lng, session)
                # 即使 Nominatim 返回 None，也写入空字符串，避免重复查询失败地址
                batch_results.append((address or "", int(structure_id)))
                logger.info(
                    "[%d] structure_id=%s → %s",
                    total_done + len(batch_results),
                    structure_id,
                    address or "(无结果)",
                )
                time.sleep(delay)

            flush_batch(conn, batch_results)
            total_done += len(batch_results)

            success = sum(1 for addr, _ in batch_results if addr)
            logger.info(
                "进度: %d / %d  （本批成功率 %d/%d）",
                total_done, effective_limit, success, len(batch_results),
            )

            if limit > 0 and total_done >= limit:
                break

        logger.info("完成。共写入 %d 条地址。", total_done)


# ─── CLI ───────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Nominatim 批量反向地理编码 — buildings.address 回填脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/reverse_geocode_addresses.py --email you@example.com --limit 100
  python scripts/reverse_geocode_addresses.py --email you@example.com
  python scripts/reverse_geocode_addresses.py --dry-run
        """,
    )
    p.add_argument(
        "--email",
        type=str,
        default=None,
        metavar="EMAIL",
        help="联系邮箱，写入 Nominatim User-Agent（Nominatim ToS 要求；--dry-run 时可不填）",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        metavar="N",
        help="最多处理 N 条（0 = 全量，默认 0）",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        metavar="N",
        help=f"每批 COMMIT 的行数（默认 {DEFAULT_BATCH_SIZE}）",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        metavar="SECS",
        help=f"两次 Nominatim 请求之间的间隔（默认 {DEFAULT_DELAY}s，Nominatim ToS 要求 ≥ 1s）",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印剩余待处理数量，不发送任何请求",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.delay < 1.0:
        sys.exit("[ERROR] --delay 不能小于 1.0s（Nominatim 使用条款）。")
    if not args.dry_run and not args.email:
        sys.exit("[ERROR] 请通过 --email your@email.com 提供联系邮箱（Nominatim ToS 要求）。")
    run(
        limit=args.limit,
        batch_size=args.batch_size,
        delay=args.delay,
        dry_run=args.dry_run,
        email=args.email,
    )
