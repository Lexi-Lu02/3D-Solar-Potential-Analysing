# Solar Map API

**3D Solar Potential Analysing** 项目的只读 HTTP 后端。为 Vue + MapLibre 前端
提供墨尔本 CBD 的建筑轮廓、屋顶光伏适宜度数据，以及按建筑计算的 kWh 估算值。

> **当前状态:** Epic 1–6 后端已完成 — 端点如下：
> `GET /health` · `/buildings/search` · `/buildings/{id}` · `/buildings/{id}/yield` ·
> `/buildings/{id}/solar` · `/buildings/{id}/impact` · `/sun/position` · `/sun/path` ·
> `/sun/psh-monthly` · `/precincts` · `/precincts/{id}`

---

## 1. 概览

| 项目 | 内容 |
|---|---|
| **技术栈** | FastAPI、psycopg3 (原生 SQL，不用 ORM)、PostgreSQL、Pydantic v2 |
| **模式** | 只读 (没有 POST/PUT/DELETE；数据库用户只有 SELECT 权限) |
| **本地 Base URL** | `http://localhost:8000/api/v1` |
| **生产 Base URL**  | `https://<域名>/api/v1` (与前端部署在同一台 EC2，前面挂 nginx) |
| **认证** | 无 — 数据为公开数据 (City of Melbourne, CC BY 4.0) |
| **自动生成的接口文档** | Swagger UI: `/api/v1/docs`，ReDoc: `/api/v1/redoc` |

本 README 是**叙述式**文档，讲清楚每个接口的用途与字段含义。如果想要交互式
"Try it out" 测试和机器可读的 schema，请运行服务后打开
`http://localhost:8000/api/v1/docs`。

本 API 服务于以下 Epic:

- **Epic 1** — 3D 城市地图 (按 ID 单条获取建筑数据)
- **Epic 2** — 建筑详情面板
- **Epic 3** — 屋顶光伏 kWh 计算引擎
- **Epic 4** — 太阳轨迹 / 阴影（Sun position API）
- **Epic 5** — Precinct 聚合（按邮编划分的 13 个片区，含建筑数量、kWh、装机缺口）
- **Epic 6** — 财务 + 环境影响（按建筑给出回本年限、CO₂ 抵消、等价树木数）

---

## 2. 快速开始

要求 Python **3.11+** (推荐 3.12)。

```bash
# 1. 进入 Backend 目录
cd Backend

# 2. 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. 安装包及开发依赖
pip install -e ".[dev]"

# 4. 配置数据库连接（.env 在 Backend 根目录）
cp .env.example .env        # Windows: copy .env.example .env
# 编辑 .env，填入 DB_HOST / DB_USER / DB_PASSWORD

# 5. 启动 API
uvicorn app.main:app --reload

# 6. 验证
curl -sf http://localhost:8000/api/v1/health
# → {"status":"ok","db":"ok","buildings_count":40951}

# 7. 运行单元测试
pytest
```

打开浏览器访问 `http://localhost:8000/api/v1/docs` 即可看到自动生成的 Swagger UI。

---

## 3. 环境变量

`.env` 放在 **`Backend/`** 根目录。所有配置从环境变量读取（开发时也支持 `.env` 文件）。
**任何必填项缺失，程序会在启动时立刻失败**。

| 变量 | 必填 | 默认 | 用途 |
|---|---|---|---|
| `DB_HOST` | ✅ | — | PostgreSQL 主机 |
| `DB_PORT` | ❌ | `5432` | PostgreSQL 端口 |
| `DB_NAME` | ✅ | — | 数据库名 |
| `DB_USER` | ✅ | — | 数据库用户。**生产环境必须使用只读角色 `solarmap_api_ro`。** |
| `DB_PASSWORD` | ✅ | — | 数据库密码 |
| `DB_POOL_MIN_SIZE` | ❌ | `1` | psycopg 连接池最小连接数 |
| `DB_POOL_MAX_SIZE` | ❌ | `10` | psycopg 连接池最大连接数 |
| `CORS_ORIGINS` | ❌ | `""` | 逗号分隔的允许来源。**生产留空**；本地前端开发时设为 `http://localhost:5173` |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

`.env` 不能提交到 git —— `.gitignore` 已排除。

---

## 4. 认证

**无。** 所有数据都是 City of Melbourne 在 CC BY 4.0 下公开的。

---

## 5. 端点列表

> **注意：** 路径参数 `{id}` 是 `buildings.id`（代理主键，整数），不是
> City of Melbourne 的 `structure_id`。

### 5.1 `GET /api/v1/health`

**用途:** 存活探针 + 数据库可达性检查。供 systemd / nginx / 监控使用，**前端不会调用**。

**响应 200**

```json
{"status": "ok", "db": "ok", "buildings_count": 40951}
```

**缓存:** `no-store`

---

### 5.2 `GET /api/v1/buildings/search`

**用途:** 按地址关键词搜索建筑，返回最多 20 条匹配结果。用于搜索框自动补全或
Epic 1 的建筑定位功能。只返回 `solar_api_cache.address` 已填充的建筑。

**查询参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `q` | string | 必填，2–200 字符 | 地址搜索词，后端执行 `ILIKE %q%` |

**响应 200**

```json
[
  {
    "id": 1,
    "structure_id": 12345,
    "lat": -37.818,
    "lng": 144.968,
    "address": "1 Collins Street, Melbourne VIC 3000"
  }
]
```

无匹配时返回空数组 `[]`，不返回 404。

**缓存:** `Cache-Control: public, max-age=300`

**curl 示例:**

```bash
curl -sf "http://localhost:8000/api/v1/buildings/search?q=Collins" | jq .
```

---

### 5.3 `GET /api/v1/buildings/{id}`

**用途:** 按 `buildings.id`（代理主键）查询单栋建筑，返回几何轮廓、高度、
屋顶信息以及光伏适宜度数据 —— Epic 2 "建筑详情面板" 所需的全部信息，
**除了** kWh 估算（在 `/yield` 端点）。

**路径参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `id` | int | `≥ 1` | `buildings.id` 代理主键 |

**响应 200**

```json
{
  "id": 1,
  "structure_id": 12345,
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[144.9680, -37.8180], [144.9691, -37.8180],
                     [144.9691, -37.8171], [144.9680, -37.8171],
                     [144.9680, -37.8180]]]
  },
  "location": {"lat": -37.8180, "lng": 144.9680},
  "footprint": {
    "roof_type": "Flat",
    "date_captured": "2018-05-28"
  },
  "height": {
    "building_height_m": 30.0,
    "base_height_m": 0.0,
    "max_elevation_m": 50.0,
    "min_elevation_m": 20.0
  },
  "solar": {
    "has_data": true,
    "dominant_rating": "Good",
    "solar_score": 75,
    "solar_score_avg": 4.0,
    "usable_ratio": 0.632,
    "usable_roof_area_m2": 60.0,
    "total_roof_area_m2": 95.0,
    "roof_patch_count": 5,
    "excellent_area_m2": 10.0
  },
  "address": "1 Collins Street, Melbourne VIC 3000"
}
```

**字段说明**

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int | `buildings.id` 代理主键 |
| `structure_id` | int | City of Melbourne 原始主键 |
| `geometry` | GeoJSON `Polygon` | 已解析的建筑轮廓，可直接喂给 MapLibre |
| `location.lat` / `location.lng` | float | WGS84 经纬度 |
| `footprint.roof_type` | string \| null | 屋顶类型（Flat / Pitched / …），来自 City of Melbourne |
| `footprint.date_captured` | ISO 日期字符串 \| null | 轮廓数据采集日期 |
| `height.building_height_m` | float | 建筑总高（用于 3D 拉伸） |
| `height.base_height_m` | float | 底部偏移 |
| `height.max_elevation_m` / `min_elevation_m` | float | 最高 / 最低点海拔 |
| `solar.has_data` | bool | 该建筑是否有任意 solar 数据（model 分或 rooftop_solar 调研） |
| `solar.dominant_rating` | string \| null | 主评级：`Excellent` / `Good` / `Moderate` / `Poor` / `Very Poor`（来自 rooftop_solar） |
| `solar.solar_score` | int (0–100) \| null | 展示用分数。**优先**取 `solar_score.predicted_score_0_100`（LightGBM 模型，见 `SolarScoreModel/`）；缺失时回退到 `round((solar_score_avg-1)/4×100)`；都没有则 null |
| `solar.solar_score_avg` | float (1–5) \| null | 屋顶调研分块的平均评分（仅 rooftop_solar 来源） |
| `solar.usable_ratio` | float (0–1) \| null | 评级在 Good 及以上的面积占比 |
| `solar.usable_roof_area_m2` | float \| null | Good 及以上评级的总面积 |
| `solar.total_roof_area_m2` | float \| null | 所有调研分块面积之和 |
| `solar.roof_patch_count` | int \| null | 调研到的屋顶分块数量 |
| `solar.excellent_area_m2` | float \| null | Excellent 评级的面积之和 |
| `address` | string \| null | 来自 `solar_api_cache.address`，由 `scripts/reverse_geocode_addresses.py` 批量填充 |

**缓存:** `Cache-Control: public, max-age=86400`

**curl 示例:**

```bash
curl -sf http://localhost:8000/api/v1/buildings/1 | jq .
```

---

### 5.4 `GET /api/v1/buildings/{id}/yield`

**用途:** 返回 12 个月的光伏发电量估算及年度合计，对应 Epic 3 "kWh 计算引擎"。

**路径参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `id` | int | `≥ 1` | `buildings.id` 代理主键 |

**响应 200 — 有光伏数据时**

```json
{
  "structure_id": 12345,
  "has_data": true,
  "kwh_annual": 13489,
  "kwh_monthly": [
    {"month": "Jan", "days": 31, "psh": 6.56, "kwh": 1829},
    {"month": "Feb", "days": 28, "psh": 5.71, "kwh": 1450}
  ],
  "assumptions": {
    "panel_efficiency": 0.20,
    "performance_ratio": 0.75,
    "peak_sun_hours_annual": 4.1,
    "usable_roof_area_m2": 60.0
  }
}
```

**kWh 计算公式**

```
kwh_monthly[i] = usable_roof_area_m2 × 0.20 × 0.75 × psh[i] × days[i]
kwh_annual = sum(kwh_monthly)
```

月度 PSH 来自 NASA POWER（20 年均值），经等比缩放使年均 = BOM 实测值 4.1 PSH/day。
详见 `app/constants/melbourne_psh.py`。

**缓存:** `Cache-Control: public, max-age=86400`

**curl 示例:**

```bash
curl -sf http://localhost:8000/api/v1/buildings/1/yield | jq '{kwh_annual, kwh_monthly}'
```

---

### 5.5 `GET /api/v1/buildings/{id}/solar`

**用途:** 返回 `solar_api_cache` 中该建筑的原始光伏 API 数据，包括最大面板数、
面板配置、碳抵消系数等。用于 Epic 1 / Epic 2 的详细光伏信息面板。

**路径参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `id` | int | `≥ 1` | `buildings.id` 代理主键 |

**响应 200**

```json
{
  "structure_id": 12345,
  "address": "1 Collins Street, Melbourne VIC 3000",
  "max_panels": 42,
  "max_array_area_m2": 84.0,
  "max_panels_kwh_annual": 15000.0,
  "max_sunshine_hours_per_year": 1496.5,
  "carbon_offset_kg_per_mwh": 0.79,
  "whole_roof_area_m2": 120.0,
  "roof_segment_stats": {"segments": 3},
  "solar_panel_configs": {"configs": []}
}
```

建筑不存在或无 `solar_api_cache` 记录时返回 **404**。

**缓存:** `Cache-Control: public, max-age=86400`

**curl 示例:**

```bash
curl -sf http://localhost:8000/api/v1/buildings/1/solar | jq '{max_panels, max_panels_kwh_annual}'
```

---

### 5.6 `GET /api/v1/sun/position` *(Epic 4)*

**用途:** 计算指定日期和时刻墨尔本 CBD 参考点的太阳高度角与方位角，替代前端原有的
客户端球面三角学实现。

**查询参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `date` | string | 必填，`YYYY-MM-DD` | 本地日期（墨尔本时区） |
| `hour` | float | 必填，0–24 | 本地时间（小数，如 `13.5` = 13:30） |

**响应 200**

```json
{
  "altitude_deg": 28.56,
  "azimuth_deg": 5.71,
  "shadow_factor": 3.15
}
```

| 字段 | 含义 |
|---|---|
| `altitude_deg` | 太阳高度角（°），低于地平线时为 0 |
| `azimuth_deg` | 太阳方位角（°），北=0，顺时针，与前端 sun-direction-line 约定一致 |
| `shadow_factor` | 相对阴影长度倍数（`90 / altitude_deg`）；太阳低于地平线时为 `null` |

**缓存:** `Cache-Control: public, max-age=31536000, immutable`（输入确定则结果永远不变）

**curl 示例:**

```bash
# 冬至正午
curl -sf "http://localhost:8000/api/v1/sun/position?date=2025-06-21&hour=12" | jq .
```

---

### 5.7 `GET /api/v1/sun/path` *(Epic 4)*

**用途:** 一次性返回某日 6:00–18:00 共 25 个采样点（每 0.5h 一条），供前端按季节
预加载并存入 sessionStorage，后续切换时间滑块无需再次请求。

**查询参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `date` | string | 必填，`YYYY-MM-DD` | 本地日期 |

**响应 200**

```json
{
  "date": "2025-12-21",
  "samples": [
    {"hour": 6.0,  "altitude_deg": 0.0,   "azimuth_deg": 112.3, "shadow_factor": null},
    {"hour": 6.5,  "altitude_deg": 3.21,  "azimuth_deg": 115.8, "shadow_factor": 28.04},
    ...
    {"hour": 18.0, "altitude_deg": 0.0,   "azimuth_deg": 248.1, "shadow_factor": null}
  ]
}
```

**缓存:** `Cache-Control: public, max-age=31536000, immutable`

**curl 示例:**

```bash
# 夏至全日轨迹（25 个采样点）
curl -sf "http://localhost:8000/api/v1/sun/path?date=2025-12-21" | jq '.samples | length'
# → 25
```

**前端集成建议：** 页面加载时并发请求三个季节日期，用 `Promise.all` 预取后缓存到
`sessionStorage`，key 格式 `sun_path_<season>`。

---

### 5.8 `GET /api/v1/sun/psh-monthly` *(Epic 4)*

**用途:** 返回墨尔本月度峰值日照时数（PSH）常量数组，供前端做季节调整 kWh 估算。

**无查询参数**

**响应 200**

```json
{
  "location": "Melbourne",
  "psh_monthly": [6.56, 5.71, 4.59, 3.18, 2.16, 1.69, 1.86, 2.61, 3.72, 4.92, 5.78, 6.49],
  "psh_annual_avg": 4.1075
}
```

索引 0 = 1月（Jan），索引 11 = 12月（Dec）。数据来自 NASA POWER（20 年均值），
经等比缩放使年均等于 BOM 站点 086338 实测值 4.1 PSH/day。

**缓存:** `Cache-Control: public, max-age=31536000, immutable`

**季节因子计算公式（前端参考）：**

```js
// 例：夏季（南半球 12/1/2 月）相对年均的倍率
const summerMonths = [11, 0, 1]  // Dec/Jan/Feb，索引从 0 开始
const seasonFactor = (
  summerMonths.reduce((s, m) => s + psh_monthly[m], 0) / summerMonths.length
) / psh_annual_avg
// kwh_seasonal ≈ base_kwh_annual × seasonFactor
```

**curl 示例:**

```bash
curl -sf http://localhost:8000/api/v1/sun/psh-monthly | jq .
```

---

### 5.9 `GET /api/v1/precincts` *(Epic 5)*

**用途:** 列出全部 13 个 precinct（按邮编划分的城市片区），按指定指标排序，返回 rank 字段供前端做 Top-5 高亮。

**查询参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `sort` | string | `kwh` / `area` / `buildings` / `gap`，默认 `kwh` | 排序键：年度 kWh、可用面积、建筑数量、装机缺口 |

**响应 200**

```json
{
  "sort": "kwh",
  "precincts": [
    {
      "precinct_id": 21640,
      "name": "Melbourne",
      "postcode": "3000",
      "total_kwh_annual": 1180607143.0,
      "total_usable_area_m2": 4957930.88,
      "installed_capacity_kw": 3469.46,
      "potential_capacity_kw": 1009990.8,
      "adoption_gap_kw": 1006521.34,
      "building_count": 4500,
      "rank": 1
    }
  ]
}
```

| 字段 | 含义 |
|---|---|
| `total_kwh_annual` | 该片区所有有数据建筑的年度 kWh 之和 |
| `total_usable_area_m2` | 评级 Good 及以上的屋顶面积之和 |
| `installed_capacity_kw` | CER 公开数据中该邮编已装机容量 |
| `potential_capacity_kw` | Google Solar API 估算的最大装机容量 |
| `adoption_gap_kw` | `potential − installed`，即仍可挖掘的装机空间 |
| `building_count` | 落入该 precinct 的建筑数量（来自 `buildings.precinct_id` 实时聚合） |
| `rank` | 按 `sort` 键的排名，1 = 最高 |

**实现说明:** `building_count` 不存储在 `precincts` 表，而是查询时通过 `buildings.precinct_id` 聚合，避免数据流水线变动后需要重跑入库。

**缓存:** `Cache-Control: public, max-age=3600`

**curl 示例:**

```bash
curl -sf "http://localhost:8000/api/v1/precincts?sort=gap" | jq '.precincts[:3]'
```

---

### 5.10 `GET /api/v1/precincts/{id}` *(Epic 5)*

**用途:** 单个 precinct 详情，附带 GeoJSON Polygon 边界，供前端渲染地图填色或弹窗。

**路径参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `precinct_id` | int | `≥ 1` | precinct 主键 |

**响应 200**

字段与 5.9 列表项一致，多出：

| 字段 | 含义 |
|---|---|
| `geo_boundary` | GeoJSON `Polygon` / `MultiPolygon`，由 PostGIS `ST_AsGeoJSON` 输出 |
| `rank` | 详情接口固定返回 `null`（rank 仅在列表里有意义） |

不存在的 `precinct_id` 返回 **404**。

**缓存:** `Cache-Control: public, max-age=3600`

**curl 示例:**

```bash
curl -sf http://localhost:8000/api/v1/precincts/21640 | jq '{name, building_count, geo_boundary: .geo_boundary.type}'
```

---

### 5.11 `GET /api/v1/buildings/{id}/impact` *(Epic 6)*

**用途:** 按建筑返回完整的财务 + 环境影响指标（系统容量、安装成本、回本年限、CO₂ 抵消、等价树木 / 汽油 / 汽车）。前端调一次拿全，不在前端复刻常量与公式。

**路径参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `id` | int | `≥ 1` | `buildings.id` 代理主键 |

**查询参数**

| 参数 | 类型 | 约束 | 默认 | 含义 |
|---|---|---|---|---|
| `season` | string | `annual` / `summer` / `autumn` / `winter` / `spring` | `annual` | 季节因子，用于按月度 PSH 调整 kWh |

**响应 200**

```json
{
  "structure_id": 12345,
  "season": "annual",
  "kwh_annual_seasonal": 9000.0,
  "kwh_annual_base": 9000.0,
  "system_size_kw": 6.2,
  "financial": {
    "installation_cost_aud": 6820,
    "annual_savings_aud": 2700,
    "payback_years": 2.5,
    "lifetime_years": 25,
    "lifetime_net_savings_aud": 60680
  },
  "environmental": {
    "annual_co2_reduction_kg": 7110,
    "co2_kg_per_kwh_used": 0.79,
    "co2_factor_source": "google_api",
    "equivalent_trees": 323,
    "equivalent_petrol_litres": 3078,
    "equivalent_cars": 1.6
  },
  "assumptions": {
    "electricity_tariff_aud_per_kwh": 0.30,
    "cost_per_kw_installed_aud": 1100,
    "self_consumption_pct": 100,
    "feed_in_tariff_included": false
  }
}
```

**字段说明**

| 字段 | 含义 |
|---|---|
| `kwh_annual_base` | `solar_api_cache.max_panels_kwh_annual`（满功率年发电量） |
| `kwh_annual_seasonal` | 按季节因子调整后的 kWh，`season=annual` 时与 base 相同 |
| `system_size_kw` | `max_panels × panel_capacity_watts ÷ 1000`，单位 kW |
| `financial.installation_cost_aud` | `system_size_kw × 1100`（Solar Choice 2025 中位数，已含 STC 补贴） |
| `financial.annual_savings_aud` | `kwh_seasonal × 0.30`（VIC 2025 简化电价，假设全自用） |
| `financial.payback_years` | 安装成本 ÷ 年节省 |
| `financial.lifetime_net_savings_aud` | `lifetime_years × annual_savings − installation_cost` |
| `environmental.co2_factor_source` | `google_api` 表示用 `solar_api_cache.carbon_offset_kg_per_mwh`；`dcceew_2024_fallback` 表示用 0.79 默认值 |
| `environmental.equivalent_trees` | 年 CO₂ ÷ 22kg（EPA AU） |
| `environmental.equivalent_petrol_litres` | 年 CO₂ ÷ 2.31kg（NGA Factors 2024） |
| `environmental.equivalent_cars` | 年 CO₂ ÷ 4500kg（澳洲平均小汽车） |

**季节因子算法:** `(sum of season's MONTHLY_PSH ÷ sum of all 12 months) × (12 ÷ months_in_season)`，结果是相对年均的归一化倍率。`annual` 恒为 1.0。

无 `solar_api_cache` 记录的建筑返回 **404**。常量集中在 `app/services/solar_impact.py` 顶部，PM 评审改这里即可。

**缓存:** `Cache-Control: public, max-age=86400`

**curl 示例:**

```bash
# 默认年度
curl -sf http://localhost:8000/api/v1/buildings/1/impact | jq '{system_size_kw, financial, environmental}'

# 夏季季节因子
curl -sf "http://localhost:8000/api/v1/buildings/1/impact?season=summer" | jq '.kwh_annual_seasonal'
```

---

## 6. 错误响应格式

所有非 2xx 响应都使用同一个外壳：

```json
{
  "error": "not_found",
  "request_id": "9f8b3a-...",
  "detail": "building 999 not found"
}
```

| HTTP 状态 | `error` 字段 | 含义 |
|---|---|---|
| 400 | `bad_request` | 参数格式错误 |
| 404 | `not_found` | 资源不存在 |
| 422 | `validation_error` | 路径/查询参数未通过 Pydantic 校验 |
| 429 | `rate_limited` | 请求频率过高 |
| 500 | `internal_error` | 未捕获的服务端异常。traceback 不会泄露给客户端 |
| 503 | `service_unavailable` | 数据库不可达 |

每个响应都带 `x-request-id` 响应头，可用于日志追踪。

---

## 7. 地址回填脚本

`scripts/reverse_geocode_addresses.py` 负责将 `solar_api_cache.address` 批量填充：

```bash
# 预览（不写库）
python scripts/reverse_geocode_addresses.py --dry-run

# 正式运行，每批 100 条
python scripts/reverse_geocode_addresses.py --batch-size 100
```

脚本遵守 Nominatim 1 req/s 限速策略。
