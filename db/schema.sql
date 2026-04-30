DROP TABLE IF EXISTS meteo;
CREATE TABLE meteo (
    data_id SERIAL PRIMARY KEY,
    time_stamp TIMESTAMPTZ NOT NULL,
    loc TEXT NOT NULL,
    temperature_2m DOUBLE PRECISION,
    shortwave_radiation DOUBLE PRECISION,
    direct_radiation DOUBLE PRECISION,
    diffuse_radiation DOUBLE PRECISION,
    wind_speed_10m DOUBLE PRECISION,
    cloud_cover DOUBLE PRECISION,
    wind_speed_10m_off DOUBLE PRECISION
);

DROP TABLE IF EXISTS entso_e_load;
CREATE TABLE entso_e_load (
    data_id SERIAL PRIMARY KEY,
    time_stamp TIMESTAMPTZ NOT NULL,
    country_code TEXT NOT NULL,
    total_load DOUBLE PRECISION
);

DROP TABLE IF EXISTS entso_e_generation;
CREATE TABLE entso_e_generation (
    data_id SERIAL PRIMARY KEY,
    time_stamp TIMESTAMPTZ NOT NULL,
    country_code TEXT NOT NULL,
    solar_generation DOUBLE PRECISION,
    wind_generation_off DOUBLE PRECISION,
    wind_generation_on DOUBLE PRECISION
    --gas_generation DOUBLE PRECISION,
    --coal_generation DOUBLE PRECISION, might be added to distinguish between different CO2 emissions
);

DROP TABLE IF EXISTS entso_e_flows;
CREATE TABLE entso_e_flows (
    data_id SERIAL PRIMARY KEY,
    time_stamp TIMESTAMPTZ NOT NULL,
    from_zone TEXT NOT NULL,
    to_zone TEXT,
    flow_mw DOUBLE PRECISION
);