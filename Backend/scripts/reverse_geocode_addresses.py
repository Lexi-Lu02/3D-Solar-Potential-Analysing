#!/usr/bin/env python3
"""
批量对建筑物进行反向地理编码，并将结果写入 solar_api_cache.address。
一次性处理所有 address 为空的记录。

用法：
    python scripts/reverse_geocode_addresses.py [--batch-size N] [--dry-run]

依赖（单独安装，不写入 pyproject.toml — 仅供离线/批处理使用）：
    pip install psycopg[binary] requests python-dotenv tqdm

环境变量（与 API 服务相同）：
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Nominatim 使用规范：
    - 最高每秒 1 次请求（本脚本已强制限速）
    - User-Agent 必须标明应用信息
    - 未经许可不得对生产环境 Nominatim 服务发起请求
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from typing import Any

import requests
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "FIT5120-3D-Solar-Potential-Analysing/1.0 (educational project)"
REQUEST_DELAY_S = 1.1  # Nominatim 限速：每秒最多 1 次请求（留 0.1s 余量）


# ---------------------------------------------------------------------------
# 数据库操作
# ---------------------------------------------------------------------------

def _get_conn():
    """从环境变量读取配置，建立 psycopg 数据库连接。"""
    import psycopg  # noqa: WPS433

    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def count_remaining(conn) -> int:
    """返回 solar_api_cache 中尚未填写地址的行数。"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM solar_api_cache WHERE address IS NULL OR address = ''"
        )
        return cur.fetchone()[0]


def fetch_all(conn, batch_size: int | None = None) -> list[dict[str, Any]]:
    """
    从 solar_api_cache 直接读取待地理编码的记录。
    使用表内自带的 center_lat / center_lng 字段，无需跨表 JOIN。
    若指定 batch_size 则只取前 N 条（用于测试），否则取全部。
    """
    with conn.cursor() as cur:
        if batch_size:
            cur.execute(
                """
                SELECT structure_id, center_lat, center_lng
                FROM solar_api_cache
                WHERE address IS NULL OR address = ''
                ORDER BY structure_id
                LIMIT %s
                """,
                (batch_size,),
            )
        else:
            cur.execute(
                """
                SELECT structure_id, center_lat, center_lng
                FROM solar_api_cache
                WHERE address IS NULL OR address = ''
                ORDER BY structure_id
                """,
            )
        rows = cur.fetchall()

    return [{"structure_id": r[0], "lat": r[1], "lng": r[2]} for r in rows]


def flush_batch(conn, updates: list[tuple[str, int]], dry_run: bool = False) -> None:
    """
    将地理编码结果批量写回 solar_api_cache。
    updates 为 (address, structure_id) 元组列表。
    """
    if dry_run:
        for address, structure_id in updates:
            logger.info("[DRY RUN] structure_id=%s → %s", structure_id, address)
        return

    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE solar_api_cache SET address = %s WHERE structure_id = %s",
            updates,
        )
    conn.commit()
    logger.debug("已提交 %d 条地址更新。", len(updates))


# ---------------------------------------------------------------------------
# Nominatim 地理编码
# ---------------------------------------------------------------------------

def reverse_geocode(lat: float, lng: float) -> str | None:
    """
    调用 Nominatim 反向地理编码接口，返回可读地址字符串。
    失败时返回 None。
    """
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "lat": lat,
                "lon": lng,
                "format": "jsonv2",
                "zoom": 18,          # 精确到街道/门牌号级别
                "addressdetails": 0,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("display_name")
    except Exception as exc:
        logger.warning("Nominatim 请求失败，坐标 (%s, %s)：%s", lat, lng, exc)
        return None


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="限制本次处理的行数（默认：不限制，处理全部）。可用于测试",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印日志，不将结果写入数据库",
    )
    args = parser.parse_args()

    # 如果存在 .env 文件则自动加载（开发环境便利）
    try:
        from dotenv import load_dotenv  # noqa: WPS433
        load_dotenv()
    except ImportError:
        pass

    logger.info("=" * 60)
    logger.info("反向地理编码脚本启动")
    logger.info("限速：%.1f 秒/条 | 模式：%s | 批次限制：%s",
                REQUEST_DELAY_S,
                "DRY RUN（不写库）" if args.dry_run else "正式写入",
                f"{args.batch_size} 条" if args.batch_size else "无限制（处理全部）")
    logger.info("=" * 60)

    logger.info("正在连接数据库...")
    conn = _get_conn()
    logger.info("数据库连接成功（host=%s, db=%s）",
                os.environ.get("DB_HOST"), os.environ.get("DB_NAME"))

    try:
        logger.info("正在统计待处理数量...")
        remaining = count_remaining(conn)
        logger.info("solar_api_cache 中待地理编码的记录共 %d 条", remaining)

        if remaining == 0:
            logger.info("所有记录均已有地址，无需处理，退出。")
            return

        estimated_seconds = remaining * REQUEST_DELAY_S
        logger.info("预计耗时约 %.0f 秒（%.1f 分钟）",
                    estimated_seconds, estimated_seconds / 60)

        logger.info("正在从数据库拉取全部待处理记录...")
        batch = fetch_all(conn, batch_size=args.batch_size)
        logger.info("成功拉取 %d 条记录，开始逐条调用 Nominatim...", len(batch))
        logger.info("-" * 60)

        succeeded = 0
        skipped = 0
        total_start = time.monotonic()

        with tqdm(total=len(batch), unit="条", dynamic_ncols=True) as pbar:
            for i, row in enumerate(batch):
                request_start = time.monotonic()

                pbar.set_description(f"structure_id={row['structure_id']}")

                address = reverse_geocode(row["lat"], row["lng"])

                if address:
                    # 每条成功后立即写入，保证中途中断时已处理的记录不丢失
                    flush_batch(conn, [(address, row["structure_id"])], dry_run=args.dry_run)
                    succeeded += 1
                    tqdm.write(f"✓ [{row['structure_id']}] {address}")
                else:
                    skipped += 1
                    tqdm.write(f"✗ [{row['structure_id']}] 未获取到地址，已跳过")

                pbar.set_postfix(成功=succeeded, 跳过=skipped)
                pbar.update(1)

                # 用实际耗时计算剩余等待时间，确保两次请求间隔不低于 REQUEST_DELAY_S
                if i < len(batch) - 1:
                    elapsed = time.monotonic() - request_start
                    wait = max(0.0, REQUEST_DELAY_S - elapsed)
                    if wait > 0:
                        time.sleep(wait)

        total_elapsed = time.monotonic() - total_start
        total_minutes = total_elapsed / 60

        logger.info("-" * 60)
        logger.info("全部处理完毕：成功 %d 条，跳过 %d 条，合计 %d 条",
                    succeeded, skipped, len(batch))
        logger.info("总耗时：%.0f 秒（%.1f 分钟）", total_elapsed, total_minutes)

        logger.info("=" * 60)
        logger.info("脚本执行完成")
        logger.info("  成功写入：%d 条", succeeded)
        logger.info("  跳过：    %d 条", skipped)
        logger.info("  总耗时：  %.0f 秒（%.1f 分钟）", total_elapsed, total_minutes)
        logger.info("=" * 60)

    finally:
        conn.close()
        logger.info("数据库连接已关闭。")


if __name__ == "__main__":
    main()