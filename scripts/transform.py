import json
import os
import pandas as pd


def clean_hourly_dataframe(raw_json):
    """Hàm trung tâm: Trải phẳng mảng JSON thành dạng bảng và chuẩn hóa cột [b0.1.2, b0.1.10]."""
    if "hourly" not in raw_json:
        return None

    # 1. Biến đổi mảng JSON thành bảng DataFrame [b0.1.10]
    df = pd.DataFrame(raw_json["hourly"])

    # 2. Chuẩn hóa tên cột khớp 100% với cấu trúc bảng PostgreSQL [b0.1.2, b0.1.8]
    df = df.rename(
        columns={
            "time": "measured_at",
            "temperature_2m": "temperature",
            "apparent_temperature": "apparent_temp",
            "precipitation": "rain",
            "surface_pressure": "pressure",
            "relative_humidity_2m": "humidity",
            "cloud_cover": "clouds",
        }
    )

    # 3. Ép kiểu dữ liệu thời gian để dễ truy vấn SQL sau này [b0.1.2, b0.1.10]
    df["measured_at"] = pd.to_datetime(df["measured_at"])

    # 4. Xử lý dữ liệu khuyết (Nội suy các ô trống nếu có lỗi trạm khí tượng) [b0.1.10]
    df = df.interpolate(method="linear")

    return df


# --- 2 HÀM ĐIỀU PHỐI RIÊNG CHO 2 MỤC TIÊU ---
def transform_history(file_path):
    """Đọc file JSON lịch sử -> Trả về DataFrame sạch để mang đi TRAIN AI [b0.1.2, b0.1.18]."""
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file lịch sử thô: {file_path}")
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        raw_json = json.load(f)
    return clean_hourly_dataframe(raw_json)


def transform_forecast(file_path):
    """Đọc file JSON dự báo hằng giờ -> Trả về DataFrame sạch để NẠP VÀO DATABASE [b0.1.2, b0.1.6]."""
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file dự báo thô: {file_path}")
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        raw_json = json.load(f)

    df = clean_hourly_dataframe(raw_json)

    # Lấy thêm thông tin city_id từ metadata mà bạn đã chèn ở api_client [b0.1.2, b0.1.8]
    if df is not None:
        city_id = raw_json.get("metadata", {}).get("city_id", None)
        df["city_id"] = city_id

    return df


# --- SỬA LẠI KHỐI LỆNH CHẠY THỬ ĐỂ GHI FILE CỨNG ---
if __name__ == "__main__":
    # Tự động tạo thư mục processed nếu máy chưa có để chặn lỗi hệ thống [b0.1.3]
    os.makedirs("data/processed", exist_ok=True)

    print("🐼 Đang xử lý biến đổi dữ liệu Lịch sử...")
    # Sửa đúng tên file sinh ra từ file api_client.py của bạn
    df_history = transform_history("data/raw/history_raw_hanoi.json")
    if df_history is not None:
        # LỆNH GHI FILE CSV CỨNG XUỐNG Ổ CỨNG [b0.1.2, b0.1.10]
        output_history_path = "data/processed/history_clean_hanoi.csv"
        df_history.to_csv(output_history_path, index=False)
        print(df_history.head(3))
        print(f"✔️ Xuất file thành công: {output_history_path}\n")

    print("⏱️ Đang xử lý biến đổi dữ liệu Dự báo hằng giờ...")
    # Sửa đúng tên file sinh ra từ file api_client.py của bạn
    df_forecast = transform_forecast("data/raw/forecast_raw_hanoi.json")
    if df_forecast is not None:
        # LỆNH GHI FILE CSV CỨNG XUỐNG Ổ CỨNG [b0.1.2, b0.1.10]
        output_forecast_path = "data/processed/forecast_clean_hanoi.csv"
        df_forecast.to_csv(output_forecast_path, index=False)
        print(df_forecast.head(3))
        print(f"✔️ Xuất file thành công: {output_forecast_path}")
