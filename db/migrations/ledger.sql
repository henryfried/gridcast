CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE ledger (
    data_id SERIAL PRIMARY KEY,
    time_stamp TIMESTAMPTZ NOT NULL CHECK (date_trunc('hour', time_stamp) = time_stamp),
    model TEXT NOT NULL,
    solar_generation_pred DOUBLE PRECISION NOT NULL,
    wind_generation_off_pred DOUBLE PRECISION NOT NULL,
    wind_generation_on_pred DOUBLE PRECISION NOT NULL,
    quantile_10 DOUBLE PRECISION,
    quantile_50 DOUBLE PRECISION,
    quantile_90 DOUBLE PRECISION,
    CHECK (quantile_10 <= quantile_50 AND quantile_50 <= quantile_90),
    situation JSONB,
    UNIQUE (time_stamp, model)   
);  