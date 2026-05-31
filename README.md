# Weather Data Pipeline

Pipeline tự động thu thập dữ liệu thời tiết theo giờ từ Open-Meteo API,
làm sạch dữ liệu và lưu vào PostgreSQL. Toàn bộ hệ thống chạy trong Docker.

---

## Mục tiêu dự án

Dự án mô phỏng quy trình xử lý dữ liệu thực tế trong môi trường Data Engineering,
bao gồm thu thập dữ liệu từ nguồn bên ngoài, xử lý dữ liệu thô, và lưu trữ
có cấu trúc vào cơ sở dữ liệu quan hệ.

---

## Kiến trúc hệ thống

    Open-Meteo API
          |
          v
    api_client.py       Thu thập dữ liệu thô, lưu vào data/raw/
          |
          v
    data_transformer.py Làm sạch dữ liệu, lưu vào data/processed/
          |
          v
    data_loader.py      Nạp dữ liệu vào PostgreSQL (Upsert)
          |
          v
    PostgreSQL (Docker) Lưu trữ dữ liệu có cấu trúc

    pipeline.py điều phối toàn bộ 3 bước trên theo thứ tự

---

## Cấu trúc thư mục

    Weather/
    ├── data/
    │   ├── raw/                  File JSON thô nhận từ API
    │   └── processed/            File CSV sau khi làm sạch
    ├── sql/
    │   └── init.sql              Tạo bảng khi PostgreSQL khởi động lần đầu
    ├── logs/
    │   └── pipeline.log          Ghi lại toàn bộ quá trình chạy pipeline
    ├── scripts/
    │   ├── api_client.py         Gọi Open-Meteo API, lưu dữ liệu thô
    │   ├── data_transformer.py   Làm sạch và chuẩn hóa dữ liệu
    │   ├── data_loader.py        Nạp dữ liệu vào PostgreSQL
    │   └── pipeline.py           Điều phối toàn bộ pipeline
    ├── .env                      Biến môi trường (không commit lên Git)
    ├── .env.example              Mẫu biến môi trường
    ├── .gitignore
    ├── docker-compose.yml        Cấu hình PostgreSQL và pipeline container
    ├── Dockerfile                Build image Python chạy pipeline
    └── requirements.txt          Danh sách thư viện Python

---

## Schema bảng weather_hourly

| Cột           | Kiểu         | Mô tả                                      |
|---------------|--------------|--------------------------------------------|
| measured_at   | TIMESTAMP    | Mốc thời gian đo, không null               |
| city_id       | INT          | ID định danh thành phố từ Open-Meteo       |
| city_name     | VARCHAR(100) | Tên thành phố                              |
| temperature   | FLOAT        | Nhiệt độ thực tế (°C)                      |
| apparent_temp | FLOAT        | Nhiệt độ cảm nhận (°C)                     |
| temp_diff     | FLOAT        | Chênh lệch cảm nhận – thực tế (°C)        |
| rain          | FLOAT        | Lượng mưa theo giờ (mm)                    |
| rain_tier     | VARCHAR(50)  | Phân loại: Không mưa / Mưa nhỏ / Mưa to   |
| pressure      | FLOAT        | Áp suất khí quyển (hPa)                    |
| humidity      | INT          | Độ ẩm tương đối (%)                        |
| clouds        | INT          | Độ phủ mây (%)                             |

Ràng buộc: `UNIQUE(city_id, measured_at)` — đảm bảo không trùng dữ liệu
khi pipeline chạy lại nhiều lần.

---

## Các bước xử lý dữ liệu

### Bước 1 - Extract (api_client.py)

Gọi Open-Meteo Forecast API lấy dự báo thời tiết 7 ngày tới (168 giờ) cho từng
thành phố trong danh sách CITIES. Dữ liệu thô được lưu dạng JSON vào data/raw/
kèm metadata gồm city_id và timestamp.

Các trường thu thập: nhiệt độ thực tế, nhiệt độ cảm nhận, lượng mưa,
áp suất khí quyển, độ ẩm, độ phủ mây.

### Bước 2 - Transform (data_transformer.py)

Làm sạch và chuẩn hóa dữ liệu thô:

- Làm phẳng JSON, đổi tên cột về dạng chuẩn
- Chuyển đổi kiểu dữ liệu (measured_at → datetime, humidity/clouds → int)
- Xử lý giá trị âm bất hợp lệ bằng clip()
- Nội suy tuyến tính cho missing values, điền median nếu vẫn còn trống
- Tính temp_diff: chênh lệch nhiệt độ cảm nhận và thực tế
- Phân loại rain_tier: Không mưa (<0.1mm), Mưa nhỏ (0.1–2mm), Mưa to (>2mm)

Kết quả xuất ra CSV vào data/processed/.

### Bước 3 - Load (data_loader.py)

Nạp dữ liệu đã xử lý vào PostgreSQL bằng Upsert:
nếu bản ghi (city_id, measured_at) đã tồn tại thì cập nhật,
chưa có thì thêm mới. Pipeline có thể chạy lại bất kỳ lúc nào mà không
tạo dữ liệu trùng lặp.

---

## Cài đặt và chạy

Yêu cầu: Python 3.10, Docker Desktop

**Bước 1** - Clone repo và tạo file .env

    cp .env.example .env

Điền thông tin vào file .env:

    DB_USER=postgres
    DB_PASSWORD=your_password
    DB_NAME=weather_db
    DB_HOST=postgres_db
    OM_api=https://api.open-meteo.com/v1/forecast

> Lưu ý: DB_HOST phải là `postgres_db` (tên service trong Docker),
> không phải `localhost`. OM_api là URL endpoint của Open-Meteo,
> không phải API key — dịch vụ này hoàn toàn miễn phí và không yêu cầu xác thực.

**Bước 2** - Cài thư viện Python

    pip install -r requirements.txt

**Bước 3** - Khởi động toàn bộ hệ thống

    docker-compose up --build

Docker Compose sẽ khởi động PostgreSQL, tự động tạo schema từ sql/init.sql,
sau đó chạy pipeline.

---

## Kiểm tra kết quả

Xem log quá trình chạy:

    cat logs/pipeline.log

Kiểm tra dữ liệu trong database:

    docker exec -it my_postgres_container psql -U postgres -d weather_db -c "SELECT * FROM weather_hourly LIMIT 5;"

---

## Thêm thành phố mới

Mở scripts/pipeline.py và thêm vào danh sách CITIES:

    CITIES = [
        {
            "name": "Tay Ninh",
            "lat": 11.3100,
            "lon": 106.0980,
            "tz": "Asia/Ho_Chi_Minh",
            "id": 1567807,
        },
        {
            "name": "Ho Chi Minh City",
            "lat": 10.8231,
            "lon": 106.6297,
            "tz": "Asia/Ho_Chi_Minh",
            "id": 1580578,
        },
    ]

Để tìm city_id và tọa độ của một thành phố mới, chạy trực tiếp:

    python scripts/api_client.py

---

## Kỹ năng thực hành trong dự án

- Xây dựng ETL pipeline với Python
- Gọi REST API và xử lý dữ liệu JSON
- Làm sạch dữ liệu chuỗi thời gian với Pandas
- Thiết kế schema PostgreSQL với index và unique constraint
- Implement Upsert với SQLAlchemy và psycopg2
- Containerize ứng dụng với Docker và Docker Compose
- Logging và error handling trong production
