# Dự án Hệ thống Tự động hóa Dữ liệu Thời tiết kết hợp AI (Weather Data & ML Pipeline)

Dự án xây dựng một đường ống dữ liệu tự động (ETL Pipeline) thu thập dữ liệu thời tiết thời gian thực, làm sạch, đưa qua mô hình học máy (Machine learning) để dự đoán hiệu chỉnh nhiệt độ và lưu trữ vào cơ sở dữ liệu PostgreSQL chạy trên Docker.

## 🛠️ Công nghệ sử dụng

* **Ngôn ngữ chính**: Python 3.12+
* **Xử lý dữ liệu**: Pandas
* **Học máy (ML)**: Scikit-learn (Thuật toán Random Forest Regressor), Joblib
* **Cơ sở dữ liệu**: PostgreSQL 15, Thư viện Psycopg2
* **Hạ tầng**: Docker, Docker Compose
* **Tự động hóa**: APScheduler
* **Nguồn dữ liệu**: Open-Meteo API (Free Geocoding, Forecast & Archive API)

## 📁 Cấu trúc thư mục dự án

```text
Weather/
├── dags/
│   └── weather_pipeline.py  # File điều phối trung tâm, chạy tự động hằng giờ
├── database/
│   └── init.sql             # File định nghĩa cấu trúc bảng SQL (Star Schema)
├── data/
│   ├── raw/                 # Nơi lưu trữ file JSON thô từ API
│   ├── processed/           # Nơi lưu trữ file CSV sạch sau khi qua Pandas
│   └── pipeline.log         # File nhật ký ghi lại lịch sử chạy ngầm của hệ thống
├── ml_core/
│   ├── saved_models/
│   │   └── weather_model.pkl # File bộ não AI sau khi đã train xong
│   └── train.py             # Kịch bản đọc dữ liệu lịch sử 1 năm để huấn luyện AI
├── scripts/
│   ├── api_client.py        # Tầng EXTRACT: Chứa các hàm gọi API (Toạ độ, Dự báo, Lịch sử)
│   ├── data_loader.py       # Tầng LOAD: Chứa hàm kết nối và chèn dữ liệu vào PostgreSQL
│   └── transform.py         # Tầng TRANSFORM: Dùng Pandas phẳng hóa JSON và làm sạch dữ liệu
├── .env                     # File lưu trữ biến môi trường (Mật khẩu DB, URL API)
├── .gitignore               # File chặn các dữ liệu rác, file nặng và bảo mật lên GitHub
└── requirements.txt         # Danh sách các thư viện cần cài đặt của dự án
```

## 🔄 Quy trình vận hành của hệ thống

Hệ thống được chia làm hai luồng hoạt động chính:

### 1. Luồng huấn luyện AI (Chạy Offline 1 lần duy nhất)

* Chạy `api_client.py` ➡️ Nhập thành phố (ví dụ: Hanoi) ➡️ Tính toán tự động bằng `datetime` để tải **1 năm dữ liệu lịch sử** về lưu thành file `.json` thô.
* Chạy `transform.py` ➡️ Dùng **Pandas** biến đổi file JSON thô thành file bảng sạch `history_clean_hanoi.csv`.
* Chạy `ml_core/train.py` ➡️ Trích xuất đặc trưng thời gian (Giờ, Tháng) ➡️ Đưa vào thuật toán **Random Forest** học quy luật biến đổi nhiệt độ ➡️ Xuất ra file bộ não tĩnh `weather_model.pkl`. Sai số đạt mức thấp (~0.77°C).

### 2. Luồng đường ống ETL tự động (Chạy hằng giờ bằng APScheduler)

* **Extract**: Trình lập lịch APScheduler kích hoạt hằng giờ ➡️ Gọi API Forecast lấy dữ liệu hiện tại và mảng mô phỏng 168 tiếng tương lai.
* **Transform**: Pandas tự động trải phẳng mảng JSON tương lai thành dạng hàng và cột, ép kiểu thời gian `DateTime`, đồng bộ khóa ngoại `city_id`.
* **ML Inference**: Hệ thống nạp các thông số độ ẩm, áp suất thô vừa làm sạch vào file `weather_model.pkl`. Con AI tự động tính toán và nhả ra cột dữ liệu mới: `predicted_temperature` (Nhiệt độ dự đoán thông minh).
* **Load**: Hệ thống kết nối vào PostgreSQL trong Docker qua thư viện `psycopg2` ➡️ Thực hiện lệnh chèn hàng loạt dữ liệu (bao gồm cả số thực tế và số AI đoán) vào bảng `weather_measurements`. Nếu trùng giờ, hệ thống tự động cập nhật đè (`ON CONFLICT DO UPDATE`) để tránh rác dữ liệu.

## 🚀 Hướng dẫn cài đặt và khởi chạy dưới máy cục bộ

### 1. Chuẩn bị môi trường

Cài đặt phần mềm **Docker Desktop** và bật ứng dụng lên trước.

### 2. Thiết lập file cấu hình `.env`

Tạo file `.env` ở thư mục gốc và điền thông số:

```text
OM_api=https://open-meteo.com
OMH_url=https://open-meteo.com
DB_USER=postgres
DB_PASSWORD=admin_password
DB_NAME=weather_pipeline
```

### 3. Kích hoạt Database PostgreSQL trên Docker

Mở Terminal tại thư mục gốc và gõ lệnh bật Database chạy ngầm:

```bash
docker-compose up -d
```

### 4. Cài đặt thư viện Python

Kích hoạt môi trường ảo `venv` và chạy lệnh cài các thư viện có trong tệp cấu hình:

```bash
pip install -r requirements.txt
```

### 5. Khởi tạo cấu trúc bảng dữ liệu

Chạy file loader để tạo tự động bảng `cities` và `weather_measurements` vào trong Docker:

```bash
python scripts/data_loader.py
```

### 6. Bật đường ống tự động chạy ngầm hằng giờ

Kích hoạt tệp điều phối chính, hệ thống sẽ chạy chu kỳ đầu tiên ngay lập tức và tự động lặp lại sau mỗi 60 phút:

```bash
python dags/weather_pipeline.py
```

Nhật ký hoạt động sẽ liên tục được cập nhật vào tệp `data/pipeline.log`.
