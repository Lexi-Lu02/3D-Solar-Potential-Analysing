"""
GET /api/v1/buildings/{id}/yield

返回 12 个月的 kWh 发电量估算及年度合计，供 Epic 3 "kWh 计算引擎" 使用。
几何、高度、光伏适宜度等建筑详情在 GET /buildings/{id} 中返回；
把 kWh 拆出来单独一个端点，是为了：
  1. 让两个端点可以独立缓存（建筑形状几乎不变；kWh 公式常量可能更新）
  2. 前端可以用 Promise.all 并发拉两个接口，哪个先到就先渲染
  3. 响应体更小，月度数据只在用户需要时才传输
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import YieldResponse
from ..services.yield_calc import BuildingNotFoundForYield, fetch_yield

router = APIRouter(prefix="/buildings", tags=["yield"])

logger = logging.getLogger(__name__)


@router.get(
    "/{id}/yield",
    response_model=YieldResponse,
    summary="按建筑 ID 获取月度及年度光伏发电量估算（Epic 3）",
    responses={
        404: {"description": "给定 id 对应的建筑不存在"},
    },
)
def get_yield(
    response: Response,
    id: int = Path(
        ...,
        ge=1,
        description="Surrogate primary key from buildings.id（正整数）",
        examples=[1],
    ),
    conn: Connection = Depends(get_conn),
) -> YieldResponse:
    # kWh 公式常量（MONTHLY_PSH、PANEL_EFFICIENCY 等）同一批数据期间不变，
    # 可以放心缓存。当常量更新时，版本化 /api/v2/ 或清除 CDN 缓存。
    response.headers["Cache-Control"] = "public, max-age=86400"

    try:
        return fetch_yield(conn, id)
    except BuildingNotFoundForYield as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"building {exc.id} not found",
        )
