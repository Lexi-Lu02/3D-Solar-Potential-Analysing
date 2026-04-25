-- Migration: split max_panels_kwh_annual into min + max
--
-- The original max_panels_kwh_annual column was incorrectly populated from
-- solarPanelConfigs[0] (the smallest config). This migration:
--   1. Renames that column to min_panels_kwh_annual (reflects what it actually is)
--   2. Adds a new max_panels_kwh_annual column (to be filled by re-crawling)

ALTER TABLE solar_api_cache
    RENAME COLUMN max_panels_kwh_annual TO min_panels_kwh_annual;

ALTER TABLE solar_api_cache
    ADD COLUMN max_panels_kwh_annual double precision;
