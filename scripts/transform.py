import json
import os
import pandas as pd


def clean_hourly_dataframe(raw_json):
    """Hàm trung tâm: Trải phẳng mảng JSON thành dạng bảng và chuẩn hóa cột."""
    if "hourly" not in raw_json:
        return None

    # 1. Biến đổi mảng JSON thành bảng DataFrame
    df = pd.DataFrame(raw_json["hourly"])

    # 2. Chuẩn hóa tên cột khớp 100% với cấu trúc bảng PostgreSQL
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

    # 3. Ép kiểu dữ liệu thời gian để dễ truy vấn SQL sau này
    df["measured_at"] = pd.to_datetime(df["measured_at"])

    # 4. Xử lý dữ liệu khuyết (Nội suy các ô trống nếu có lỗi trạm khí tượng)
    df = df.interpolate(method="linear")

    return df


# --- 2 HÀM ĐIỀU PHỐI RIÊNG CHO 2 MỤC TIÊU ---
def transform_history(file_path):
    """Đọc file JSON lịch sử -> Trả về DataFrame sạch để mang đi TRAIN AI."""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        raw_json = json.load(f)
    return clean_hourly_dataframe(raw_json)


def transform_forecast(file_path):
    """Đọc file JSON dự báo hằng giờ -> Trả về DataFrame sạch để NẠP VÀO DATABASE."""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        raw_json = json.load(f)

    df = clean_hourly_dataframe(raw_json)

    # Lấy thêm thông tin city_id từ metadata mà bạn đã chèn ở api_client
    if df is not None:
        city_id = raw_json.get("metadata", {}).get("city_id", None)
        df["city_id"] = city_id

    return df


if __name__ == "__main__":
    # CHẠY THỬ NGHIỆM BÓC TÁCH FILE LỊCH SỬ ĐỂ TRAIN
    print("🐼 Đang thử nghiệm biến đổi dữ liệu Lịch sử...")
    df_history = transform_history("data/raw/history_raw_hanoi.json")
    if df_history is not None:
        print(df_history.head(3))
        print(f"✔️ Trích xuất thành công {len(df_history)} hàng lịch sử.\n")

    # CHẠY THỬ NGHIỆM BÓC TÁCH FILE DỰ BÁO HẰNG GIỜ
    print("⏱️ Đang thử nghiệm biến đổi dữ liệu Dự báo hằng giờ...")
    df_forecast = transform_forecast("data/raw/forecast_raw_hanoi.json")
    if df_forecast is not None:
        print(df_forecast.head(3))
        print(f"✔️ Trích xuất thành công {len(df_forecast)} hàng dự báo.")
