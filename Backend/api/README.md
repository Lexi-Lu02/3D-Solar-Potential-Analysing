# Solar Map API

**3D Solar Potential Analysing** 项目的只读 HTTP 后端。为 Vue + MapLibre 前端
提供墨尔本 CBD 的建筑轮廓、屋顶光伏适宜度数据,以及按建筑计算的 kWh 估算值。

> **当前状态:** Phase B 已完成 — 实现了 `/health` 与 `/buildings/{id}` 两个端点。
> Phase C–E 将依次加入 kWh 月度估算 (`/yield`)、地址回填、EC2 部署。完整路线图见
> `C:\Users\Flame\.claude\plans\` 中的实施计划。

---

## 1. 概览

| 项目 | 内容 |
|---|---|
| **技术栈** | FastAPI、psycopg3 (原生 SQL,不用 ORM)、PostgreSQL、Pydantic v2 |
| **模式** | 只读 (没有 POST/PUT/DELETE;数据库用户只有 SELECT 权限) |
| **本地 Base URL** | `http://localhost:8000/api/v1` |
| **生产 Base URL**  | `https://<域名>/api/v1` (与前端部署在同一台 EC2,前面挂 nginx) |
| **认证** | 无 — 数据为公开数据 (City of Melbourne, CC BY 4.0) |
| **自动生成的接口文档** | Swagger UI: `/api/v1/docs`,ReDoc: `/api/v1/redoc` |

本 README 是**叙述式**文档,讲清楚每个接口的用途与字段含义。如果想要交互式
"Try it out" 测试和机器可读的 schema,请运行服务后打开
`http://localhost:8000/api/v1/docs`。那个页面是从同一份 Pydantic 模型生成的,
和 API 实际返回的形状不可能脱节。

本 API 服务于项目计划中的以下 Epic:

- **Epic 1** — 3D 城市地图 (按 ID 单条获取建筑数据)
- **Epic 2** — 建筑详情面板
- **Epic 3** — 屋顶光伏 kWh 计算引擎

---

## 2. 快速开始

要求 Python **3.11+** (推荐 3.12)。

```bash
# 1. 克隆并进入 api 目录
cd Backend/api

# 2. 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. 安装包及开发依赖
pip install -e ".[dev]"

# 4. 配置数据库连接
cp .env.example .env        # Windows: copy .env.example .env
# 然后编辑 .env 填入 DB_HOST / DB_USER / DB_PASSWORD

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

所有配置都从环境变量读取 (开发时也支持 `.env` 文件)。**任何必填项缺失,
程序会在启动时立刻失败** —— 这是有意为之,与其在第一个请求时神秘报错,
不如在启动时直接拒绝运行。

| 变量 | 必填 | 默认 | 用途 |
|---|---|---|---|
| `DB_HOST` | ✅ | — | PostgreSQL 主机 (例如 `16.176.25.174`) |
| `DB_PORT` | ❌ | `5432` | PostgreSQL 端口 |
| `DB_NAME` | ✅ | — | 数据库名 (例如 `melbourne_solar`) |
| `DB_USER` | ✅ | — | 数据库用户。**生产环境必须使用只读角色 `solarmap_api_ro`。** |
| `DB_PASSWORD` | ✅ | — | 数据库密码 |
| `DB_POOL_MIN_SIZE` | ❌ | `1` | psycopg 连接池最小连接数 |
| `DB_POOL_MAX_SIZE` | ❌ | `10` | psycopg 连接池最大连接数 |
| `CORS_ORIGINS` | ❌ | `""` | 逗号分隔的允许来源列表。**生产环境留空** (前端和 API 共享同一个 nginx → 同源 → 不需要 CORS)。本地前端开发时设为 `http://localhost:5173`。 |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

`.env` 不能提交到 git —— `.gitignore` 已经把它排除了。

---

## 4. 认证

**无。** 所有数据都是 City of Melbourne 在 CC BY 4.0 下公开的,API 不暴露任何
用户相关信息。如果未来某个迭代加入了用户态 (收藏建筑等),会在这里补充认证说明。

---

## 5. 端点列表

> 以下是当前已实现的端点。Phase C 完成后会再加入 `/buildings/{id}/yield`。

### 5.1 `GET /api/v1/health`

**用途:** 存活探针 + 数据库可达性检查。供 systemd / nginx / 监控使用,
**前端不会调用**。

**Epic:** 运维 / 监控

**路径参数:** 无
**查询参数:** 无

**响应 200**

```json
{
  "status": "ok",
  "db": "ok",
  "buildings_count": 40951
}
```

| 字段 | 类型 | 含义 |
|---|---|---|
| `status` | `"ok"` \| `"error"` | 服务总体健康状态 |
| `db` | `"ok"` \| `"unreachable"` | API 是否能从 PostgreSQL 中 SELECT |
| `buildings_count` | int | `buildings` 表当前的实时行数 |

**响应 503** —— 数据库不可达或查询失败:

```json
{
  "status": "error",
  "db": "unreachable",
  "buildings_count": 0
}
```

**缓存:** `no-store`
**频率限制:** 无

**curl 示例:**

```bash
curl -sf http://localhost:8000/api/v1/health | jq .
```

---

### 5.2 `GET /api/v1/buildings/{structure_id}`

**用途:** 按 City of Melbourne 的 `structure_id` 查询单栋建筑,返回几何轮廓、
高度、屋顶面积以及光伏适宜度数据 —— 也就是 Epic 2 "建筑详情面板" 需要的全部
信息,**除了** kWh 估算 (放在 `/yield` 端点中,见 Phase C)。

之所以拆成两个端点,是为了让响应体足够小,并允许前端独立缓存:打开详情面板时,
前端可以并发拉这两个接口 (`Promise.all`),哪个先到就先渲染哪个区块。

**Epic:** Epic 1 (按 ID 拉建筑数据), Epic 2 (建筑详情面板)

**路径参数**

| 参数 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `structure_id` | int | `≥ 1` | City of Melbourne 主键 |

**查询参数:** 无

**响应 200**

```json
{
  "structure_id": 12345,
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [144.9680, -37.8180],
      [144.9691, -37.8180],
      [144.9691, -37.8171],
      [144.9680, -37.8171],
      [144.9680, -37.8180]
    ]]
  },
  "location": {
    "lat": -37.8180,
    "lng": 144.9680
  },
  "footprint": {
    "footprint_area_m2": 9987.4,
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
  "address": null
}
```

**字段说明**

| 字段 | 类型 | 含义 |
|---|---|---|
| `structure_id` | int | City of Melbourne 主键 |
| `geometry` | GeoJSON `Polygon` | 已解析的建筑轮廓,可直接喂给 MapLibre |
| `location.lat` / `location.lng` | float | WGS84 经纬度 |
| `footprint.footprint_area_m2` | float | 屋顶 2D 投影面积,服务端用球面 shoelace 公式从 `geo_shape` 实时算出。与 `Data wrangling/build_geojson.py` 保持一致 |
| `footprint.roof_type` | string \| null | 屋顶类型标签 (Flat / Pitched / …),来自 City of Melbourne |
| `footprint.date_captured` | ISO 日期字符串 \| null | 该轮廓数据采集日期 |
| `height.building_height_m` | float | 建筑总高 (用于 3D 拉伸) |
| `height.base_height_m` | float | 底部偏移 |
| `height.max_elevation_m` / `min_elevation_m` | float | 最高 / 最低点海拔 |
| `solar.has_data` | bool | 是否匹配到了屋顶光伏调研数据。约 5% 的建筑没有匹配到任何调研多边形 |
| `solar.dominant_rating` | string \| null | 主评级:`Excellent` / `Good` / `Moderate` / `Poor` / `Very Poor` |
| `solar.solar_score` | int (0–100) \| null | 0–100 的展示用分数,由 `solar_score_avg` 线性映射而来 |
| `solar.solar_score_avg` | float (1–5) \| null | 屋顶调研分块的平均评分 (1–5) |
| `solar.usable_ratio` | float (0–1) \| null | 评级在 Good 及以上的屋顶面积占比 |
| `solar.usable_roof_area_m2` | float \| null | 评级在 Good 及以上的屋顶面积总和 |
| `solar.total_roof_area_m2` | float \| null | 所有调研屋顶分块面积之和 |
| `solar.roof_patch_count` | int \| null | 调研到的屋顶分块数量 |
| `solar.excellent_area_m2` | float \| null | 仅 Excellent 评级的面积之和 |
| `address` | string \| null | 反向地理编码出的街道地址。**Phase D 之前永远为 `null`**,Phase D 用 Nominatim 批量回填后才会有值 |

**没有数据时的字段处理**

如果该建筑没有匹配到屋顶光伏调研 (`has_data: false`),`solar` 下除 `has_data`
外的所有字段都会是 `null`,而不是 `0`。前端需要据此判断该不该显示
"光伏适宜度" 区块。`footprint`、`height`、`location`、`geometry` 不受影响。

**响应 404** —— 建筑不存在:

```json
{
  "error": "not_found",
  "request_id": "9f8b3a-...",
  "detail": "building 99999999 not found"
}
```

**响应 422** —— 路径参数不合法 (非整数,或 ≤ 0):

```json
{
  "error": "validation_error",
  "request_id": "9f8b3a-...",
  "detail": "..."
}
```

**缓存:** `Cache-Control: public, max-age=86400`
建筑数据在数据回填周期内 (天级别) 都是不变的,可以放心让浏览器和 nginx 长缓存。
当数据管线重新生成 GeoJSON / 重新导入 PG 时,记得清缓存或改 URL。

**频率限制:** 当前未启用按端点限速。Phase E 上线时会在 nginx 层加一个 IP 维度
的全局限速 (例如 60 req/min/IP)。

**curl 示例:**

```bash
curl -sf http://localhost:8000/api/v1/buildings/12345 | jq .
```

---

## 6. 错误响应格式

所有非 2xx 响应都使用同一个外壳,带一个 `request_id`,可以拿去 grep 服务端日志:

```json
{
  "error": "internal_error",
  "request_id": "9f8b3a-...",
  "detail": "可选的人类可读说明"
}
```

| HTTP 状态 | `error` 字段 | 含义 |
|---|---|---|
| 400 | `bad_request` | 请求体或参数格式错误 |
| 404 | `not_found` | 资源 (例如某个建筑) 不存在 |
| 422 | `validation_error` | 入参没通过 Pydantic 校验 (例如 `structure_id` 不是整数) |
| 429 | `rate_limited` | 该 IP 请求过于频繁 |
| 500 | `internal_error` | 未捕获的服务端异常。**Python 的 traceback 永远不会泄露给客户端**,需要排查时按 `request_id` 去 journalctl 中查 |
| 503 | `service_unavailable` | 数据库不可达或下游故障 |

每个响应都会带一个 `x-request-id` 头,值取自上游代理传入的 `X-Request-ID`,
没有则服务端生成一个新的。这样即使客户端没解析 JSON,也能从 header 中拿到请求 ID。