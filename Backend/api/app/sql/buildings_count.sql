-- Health probe: cheap row count for the buildings table.
-- Used by GET /api/v1/health to confirm the API can both reach PG and read
-- the expected schema.
SELECT count(*) AS n FROM buildings;
