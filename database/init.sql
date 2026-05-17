-- 1. Tạo bảng chiều lưu thông tin các thành phố (Dimension Table)
CREATE TABLE
IF NOT EXISTS cities
(
    id INT PRIMARY KEY,
    name VARCHAR
(100) NOT NULL,
    country VARCHAR
(100),
    latitude NUMERIC
(9,6) NOT NULL,
    longitude NUMERIC
(9,6) NOT NULL,
    timezone VARCHAR
(50) DEFAULT 'auto'
);

-- 2. Tạo bảng sự kiện lưu chỉ số thời tiết theo giờ (Fact Table)
CREATE TABLE
IF NOT EXISTS weather_measurements
(
    id SERIAL PRIMARY KEY,
    city_id INT REFERENCES cities
(id) ON
DELETE CASCADE,
    measured_at TIMESTAMP
NOT NULL,
    temperature NUMERIC
(5,2),          -- Nhiệt độ thực tế từ API Open-Meteo
    predicted_temperature NUMERIC
(5,2),-- PHẦN MỞ RỘNG: Nhiệt độ do AI của bạn dự đoán
    apparent_temp NUMERIC
(5,2),
    rain NUMERIC
(5,2),
    pressure NUMERIC
(6,1),
    humidity INT,
    clouds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Đảm bảo không lưu trùng dữ liệu của cùng một thành phố tại cùng một giờ
    CONSTRAINT unique_city_time UNIQUE
(city_id, measured_at)
);
