CREATE TABLE IF NOT EXISTS weather_hourly (
    measured_at   TIMESTAMP    NOT NULL,
    city_id       INT          NOT NULL,
    city_name     VARCHAR(100),
    temperature   FLOAT,
    apparent_temp FLOAT,
    temp_diff     FLOAT,
    rain          FLOAT,
    rain_tier     VARCHAR(50),
    pressure      FLOAT,
    humidity      INT,
    clouds        INT,

    -- Cài cắm ràng buộc bắt buộc để hàm Upsert hoạt động --
    CONSTRAINT uq_city_time UNIQUE (city_id, measured_at)
);

CREATE INDEX IF NOT EXISTS idx_city_id  ON weather_hourly(city_id);
CREATE INDEX IF NOT EXISTS idx_measured ON weather_hourly(measured_at);
