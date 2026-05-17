-- 1. Bảng lưu danh sách thành phố
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

-- 2. Bảng lưu chỉ số thời tiết chi tiết theo giờ
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
(5,2),          -- Nhiệt độ thực tế từ API
    predicted_temperature NUMERIC
(5,2),-- Nhiệt độ do mô hình AI tự tính toán
    apparent_temp NUMERIC
(5,2),
    rain NUMERIC
(5,2),
    pressure NUMERIC
(6,1),
    humidity INT,
    clouds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Chặn trùng lặp dữ liệu của cùng một thành phố tại cùng một mốc giờ
    CONSTRAINT unique_city_time UNIQUE
(city_id, measured_at)
);
