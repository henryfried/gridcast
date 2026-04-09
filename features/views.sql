DROP VIEW IF EXISTS net_load CASCADE;
DROP VIEW IF EXISTS v_weather_generation;
DROP VIEW IF EXISTS v_grid_balance;
DROP VIEW IF EXISTS v_renewable_share;


CREATE VIEW net_load AS
    WITH hourly_load AS (
        SELECT
            DATE_TRUNC('hour', time_stamp) AS hourly,
            country_code,
            AVG(total_load) AS avg_load_mw
        FROM entso_e_load
        GROUP BY hourly, country_code
    )
    SELECT
        h.hourly,
        h.country_code,
        h.avg_load_mw,
        g.solar_generation,
        g.wind_generation_off,
        g.wind_generation_on,
        h.avg_load_mw - (g.solar_generation + g.wind_generation_off + g.wind_generation_on) AS net_load_mw
FROM hourly_load h
JOIN entso_e_generation g ON h.hourly = g.time_stamp AND h.country_code = g.country_code;


CREATE VIEW v_renewable_share AS
    SELECT
        n.hourly,
        n.avg_load_mw,
        n.solar_generation,
        n.solar_generation + n.wind_generation_off + n.wind_generation_on AS renewable_total_mw,
        (n.solar_generation + n.wind_generation_off + n.wind_generation_on) / n.avg_load_mw AS renewable_share_percent
FROM net_load n;

CREATE VIEW v_grid_balance AS
    SELECT
        n.hourly,
        n.country_code,
        n.avg_load_mw,
        n.net_load_mw - SUM(e.flow_mw) AS net_balance
FROM net_load n
JOIN entso_e_flows e ON n.hourly = e.time_stamp
GROUP BY n.hourly, n.country_code, n.avg_load_mw, n.net_load_mw;


CREATE VIEW v_weather_generation AS
    WITH de_lu_weather AS (
        SELECT
            DATE_TRUNC('hour', time_stamp) AS hourly,
            AVG(temperature_2m) AS avg_temperature_2m,
            AVG(shortwave_radiation) AS avg_shortwave_radiation,
            AVG(diffuse_radiation) AS avg_diffuse_radiation,
            AVG(wind_speed_10m) AS avg_wind_speed_10m,
            AVG(cloud_cover) AS avg_cloud_cover
        FROM meteo
        GROUP BY hourly
    )
    SELECT
        w.hourly,
        w.avg_temperature_2m,
        w.avg_shortwave_radiation,
        w.avg_diffuse_radiation,
        w.avg_wind_speed_10m,
        w.avg_cloud_cover,
        e.solar_generation,
        e.wind_generation_off,
        e.wind_generation_on
FROM de_lu_weather w
JOIN entso_e_generation e ON w.hourly = e.time_stamp;

CREATE VIEW v_forecast_features AS
SELECT
    b.hourly,
    b.country_code,
    b.net_balance,
    g.avg_temperature_2m,
    g.avg_shortwave_radiation,
    g.avg_diffuse_radiation,
    g.avg_wind_speed_10m,
    g.avg_cloud_cover,
    g.solar_generation,
    g.wind_generation_off,
    g.wind_generation_on,
    (g.solar_generation + g.wind_generation_off + g.wind_generation_on) / b.avg_load_mw AS renewable_share_percent
FROM v_weather_generation g
JOIN v_grid_balance b ON g.hourly = b.hourly;