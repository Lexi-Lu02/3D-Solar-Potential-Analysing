"""
Melbourne Solar Data Processing Pipeline
========================================
输入文件:
  - mga55_gda95_green_roof_solar.shp (.shx .dbf .prj 需在同目录)
  - 2023-building-footprints.csv

输出文件:
  - buildings_full.csv       → 导入 PostgreSQL buildings 表
  - rooftop_solar_full.csv   → 导入 PostgreSQL rooftop_solar 表

依赖:
  pip install geopandas pandas shapely pyproj
"""

import geopandas as gpd
import pandas as pd
from shapely import from_geojson
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 路径配置（按需修改）
# ============================================================
SOLAR_SHP   = 'mga55_gda95_green_roof_solar.shp'
BUILDINGS_CSV = '2023-building-footprints.csv'
OUTPUT_BUILDINGS   = 'buildings_full.csv'
OUTPUT_SOLAR       = 'rooftop_solar_full.csv'


# ============================================================
# Step 1: 读取原始数据
# ============================================================
print("【1】读取数据...")
solar        = gpd.read_file(SOLAR_SHP)
buildings_raw = pd.read_csv(BUILDINGS_CSV)
print(f"  Solar屋顶多边形: {len(solar)} 行")
print(f"  Building Footprints: {len(buildings_raw)} 行")


# ============================================================
# Step 2: 清洗 Building Footprints
# ============================================================
print("【2】清洗 Building Footprints...")

# 将 GeoJSON 字符串转为几何对象，并转换坐标系到 EPSG:28355（与Solar一致）
buildings_raw['geometry'] = buildings_raw['Geo Shape'].apply(from_geojson)
buildings_gdf = gpd.GeoDataFrame(
    buildings_raw, geometry='geometry', crs='EPSG:4326'
).to_crs('EPSG:28355')

# 提取经纬度
buildings_raw[['lat', 'lng']] = (
    buildings_raw['Geo Point']
    .str.split(', ', expand=True)
    .astype(float)
)

# 日期格式化：20180528 → 2018-05-28
buildings_raw['date_captured'] = pd.to_datetime(
    buildings_raw['date_captured'].astype(str), format='%Y%m%d'
)

# 只保留 Structure 类型（去掉围墙、附属设施等）
buildings_clean = buildings_raw[
    buildings_raw['footprint_type'] == 'Structure'
].copy()
print(f"  过滤后建筑数: {len(buildings_clean)} (原 {len(buildings_raw)})")


# ============================================================
# Step 3: 清洗 Solar Shapefile
# ============================================================
print("【3】清洗 Solar 数据...")

# RATING 文字转数字评分
rating_map = {
    'Excellent': 5,
    'Good':      4,
    'Moderate':  3,
    'Poor':      2,
    'Very Poor': 1,
}
solar['solar_score'] = solar['RATING'].map(rating_map)

# 过滤极小噪点多边形（< 4 m²）
solar_clean = solar[solar['Shape_Area'] >= 4].copy()
print(f"  过滤后屋顶多边形: {len(solar_clean)} (原 {len(solar)})")


# ============================================================
# Step 4: 空间叠加 — 每块屋顶匹配到对应建筑
# ============================================================
print("【4】空间叠加：屋顶多边形 → 建筑...")

joined = gpd.sjoin(
    solar_clean,
    buildings_gdf[['structure_id', 'geometry']],
    how='left',
    predicate='intersects'   # 用 intersects 而非 within，匹配率更高
)

# 一块屋顶可能与多栋建筑相交，只保留第一个匹配
joined = joined[~joined.index.duplicated(keep='first')]

matched_count = joined['structure_id'].notna().sum()
print(f"  匹配率: {matched_count / len(joined) * 100:.1f}%")


# ============================================================
# Step 5: 按建筑聚合 Solar 数据
# ============================================================
print("【5】按建筑聚合...")

matched = joined[joined['structure_id'].notna()].copy()
matched['structure_id'] = matched['structure_id'].astype(int)

solar_agg = matched.groupby('structure_id').agg(
    # 该建筑所有屋顶分块的总面积
    total_roof_area  = ('Shape_Area', 'sum'),
    # 可用面积：只统计评分 >= 4（Good 及以上）的分块
    usable_roof_area = ('Shape_Area', lambda x:
                        x[matched.loc[x.index, 'solar_score'] >= 4].sum()),
    # 主评级：出现次数最多的 RATING
    dominant_rating  = ('RATING', lambda x: x.value_counts().index[0]),
    # 平均评分（1-5）
    solar_score_avg  = ('solar_score', 'mean'),
    # 屋顶分块数量
    roof_patch_count = ('Shape_Area', 'count'),
    # Excellent 面积
    excellent_area   = ('Shape_Area', lambda x:
                        x[matched.loc[x.index, 'solar_score'] == 5].sum()),
).reset_index()

# 精度处理
solar_agg['usable_ratio']     = (solar_agg['usable_roof_area'] / solar_agg['total_roof_area']).round(3)
solar_agg['solar_score_avg']  = solar_agg['solar_score_avg'].round(2)
solar_agg['total_roof_area']  = solar_agg['total_roof_area'].round(1)
solar_agg['usable_roof_area'] = solar_agg['usable_roof_area'].round(1)
solar_agg['excellent_area']   = solar_agg['excellent_area'].round(1)

print(f"  汇总建筑数: {len(solar_agg)}")


# ============================================================
# Step 6: 构建最终 buildings 表
# ============================================================
print("【6】构建 buildings 表...")

buildings_table = buildings_clean[[
    'structure_id',
    'lat', 'lng',
    'roof_type',
    'footprint_type',
    'structure_extrusion',    # 建筑总高度（3D渲染用）
    'footprint_extrusion',    # 建筑底部高度
    'structure_max_elevation',
    'structure_min_elevation',
    'date_captured',
    'Geo Shape',              # GeoJSON 轮廓字符串
]].copy()

buildings_table.rename(columns={
    'Geo Shape':               'geo_shape',
    'structure_extrusion':     'building_height',
    'footprint_extrusion':     'base_height',
    'structure_max_elevation': 'max_elevation',
    'structure_min_elevation': 'min_elevation',
}, inplace=True)

print(f"  buildings行数: {len(buildings_table)}")


# ============================================================
# Step 7: 导出 CSV
# ============================================================
print("【7】导出 CSV...")
buildings_table.to_csv(OUTPUT_BUILDINGS, index=False)
solar_agg.to_csv(OUTPUT_SOLAR, index=False)

print(f"\n✅ 完成！")
print(f"  {OUTPUT_BUILDINGS}:  {len(buildings_table)} 行, 字段: {list(buildings_table.columns)}")
print(f"  {OUTPUT_SOLAR}: {len(solar_agg)} 行, 字段: {list(solar_agg.columns)}")
