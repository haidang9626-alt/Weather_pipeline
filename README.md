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
    data_loader.py      Nạp dữ liệu vào PostgreSQL
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
    ├── database/
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
    ├── docker-compose.yml        Cấu hình PostgreSQL container
    ├── Dockerfile                Build image Python chạy pipeline
    └── requirements.txt          Danh sách thư viện Python

---

## Các bước xử lý dữ liệu

### Bước 1 - Extract (api_client.py)

Gọi Open-Meteo API lấy dự báo thời tiết 7 ngày tới theo giờ cho một thành phố.
Dữ liệu thô được lưu dưới dạng JSON vào thư mục data/raw/.

Các trường dữ liệu thu thập:

- Nhiệt độ thực tế và nhiệt độ cảm nhận
- Lượng mưa theo giờ
- Áp suất khí quyển
- Độ ẩm và độ phủ mây

### Bước 2 - Transform (data_transformer.py)

Làm sạch và chuẩn hóa dữ liệu thô:

- Đổi tên cột về dạng chuẩn
- Chuyển đổi kiểu dữ liệu
- Xử lý giá trị âm bất hợp lệ bằng clip
- Nội suy tuyến tính cho missing values
- Tính chênh lệch nhiệt độ cảm nhận và thực tế
- Phân loại mức độ mưa: Không mưa, Mưa nhỏ, Mưa to

### Bước 3 - Load (data_loader.py)

Nạp dữ liệu đã xử lý vào PostgreSQL.
Sử dụng Upsert thay vì Insert thông thường để tránh duplicate
khi pipeline chạy lại nhiều lần.

---

## Cài đặt và chạy

Yêu cầu: Python 3.10, Docker Desktop

Bước 1 - Clone repo và tạo file .env

    cp .env.example .env

Điền thông tin vào file .env

    DB_USER=postgres
    DB_PASSWORD=your_password
    DB_NAME=weather_db
    DB_HOST=localhost
    OM_api=https://api.open-meteo.com/v1/forecast

Bước 2 - Cài thư viện Python

    pip install -r requirements.txt

Bước 3 - Khởi động PostgreSQL

    docker-compose up -d postgres_db

Bước 4 - Chạy pipeline

    python scripts/pipeline.py

---

## Kiểm tra kết quả

Xem log quá trình chạy

    cat logs/pipeline.log

Kiểm tra dữ liệu trong database

    docker exec -it my_postgres_container psql -U postgres -d weather_db -c "SELECT * FROM weather_hourly LIMIT 5;"

---

## Thêm thành phố mới

Mở scripts/pipeline.py và thêm vào danh sách CITIES

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

---

## Kỹ năng thực hành trong dự án

- Xây dựng ETL pipeline với Python
- Gọi REST API và xử lý dữ liệu JSON
- Làm sạch dữ liệu chuỗi thời gian với Pandas
- Thiết kế schema PostgreSQL với index và unique constraint
- Containerize ứng dụng với Docker và Docker Compose
- Logging và error handling trong production
