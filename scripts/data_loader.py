import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Hàm thiết lập kết nối tới cơ sở dữ liệu PostgreSQL trong Docker container [b0.1.2, b0.1.6, b0.1.7]."""
    try:
        conn = psycopg2.connect(
            host="localhost",  # Vì Docker mở cổng ra máy cục bộ
            port="5432",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "admin_password"),
            database=os.getenv("DB_NAME", "weather_pipeline"),
        )
        return conn
    except Exception as e:
        print(f"❌ Không thể kết nối tới PostgreSQL: {e}")
        return None


def init_database():
    """Đọc file init.sql và tự động tạo các bảng vào Database nếu chưa có."""
    conn = get_db_connection()
    if not conn:
        return

    sql_path = "database/init.sql"
    if not os.path.exists(sql_path):
        print(f"❌ Không tìm thấy file định nghĩa cấu trúc SQL tại: {sql_path}")
        conn.close()
        return

    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        cursor = conn.cursor()
        cursor.execute(sql_script)
        conn.commit()
        print("✔️ Khởi tạo các bảng dữ liệu SQL (cities, weather_measurements) thành công!")
        cursor.close()
    except Exception as e:
        print(f"❌ Lỗi khi khởi tạo cấu trúc bảng: {e}")
        conn.rollback()
    finally:
        conn.close()


def insert_city(conn, city_data):
    """
    Chèn thông tin thành phố vào bảng 'cities' (Dimension table).
    city_data là một Dictionary chứa thông tin thành phố lấy từ API Geocoding.
    """
    sql = """
    INSERT INTO cities (id, name, country, latitude, longitude, timezone)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        country = EXCLUDED.country,
        timezone = EXCLUDED.timezone;
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            sql,
            (
                city_data.get("id"),
                city_data.get("name"),
                city_data.get("country", "Không rõ"),
                city_data.get("latitude"),
                city_data.get("longitude"),
                city_data.get("timezone", "auto"),
            ),
        )
        conn.commit()
        cursor.close()
        print(f"📌 Đã đồng bộ thành phố: {city_data.get('name')} vào bảng SQL.")
    except Exception as e:
        print(f"❌ Lỗi khi chèn thành phố vào DB: {e}")
        conn.rollback()


def insert_weather_dataframe(conn, df_clean):
    """
    Nhận bảng DataFrame sạch từ Pandas và chèn hàng loạt vào bảng 'weather_measurements' (Fact table).
    """
    if df_clean is None or df_clean.empty:
        print("⚠️ Bảng dữ liệu sạch trống rỗng, bỏ qua bước Load.")
        return

    # Câu lệnh INSERT kết hợp ON CONFLICT để ghi đè nếu trùng giờ (Idempotent Pipeline)
    sql = """
    INSERT INTO weather_measurements (city_id, measured_at, temperature, apparent_temp, rain, pressure, humidity, clouds)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (city_id, measured_at) DO UPDATE SET
        temperature = EXCLUDED.temperature,
        apparent_temp = EXCLUDED.apparent_temp,
        rain = EXCLUDED.rain,
        pressure = EXCLUDED.pressure,
        humidity = EXCLUDED.humidity,
        clouds = EXCLUDED.clouds;
    """

    try:
        cursor = conn.cursor()
        count = 0

        # Duyệt qua từng dòng trong bảng Pandas DataFrame để chèn vào SQL
        for _, row in df_clean.iterrows():
            # Đề phòng trường hợp khuyết khóa ngoại city_id
            if pd.isna(row["city_id"]):
                continue

            cursor.execute(
                sql,
                (
                    int(row["city_id"]),
                    row["measured_at"].to_pydatetime(),  # Chuyển đổi timestamp Pandas sang Datetime Python chuẩn
                    row["temperature"]
                    if not pd.isna(row["temperature"])
                    else None,
                    row["apparent_temp"]
                    if not pd.isna(row["apparent_temp"])
                    else None,
                    row["rain"] if not pd.isna(row["rain"]) else None,
                    row["pressure"] if not pd.isna(row["pressure"]) else None,
                    int(row["humidity"]) if not pd.isna(row["humidity"]) else None,
                    int(row["clouds"]) if not pd.isna(row["clouds"]) else None,
                ),
            )
            count += 1

        conn.commit()
        cursor.close()
        print(f"✔️ Đã nạp thành công {count} dòng dữ liệu thời tiết sạch vào PostgreSQL!")
    except Exception as e:
        print(f"❌ Lỗi khi nạp dữ liệu DataFrame vào DB: {e}")
        conn.rollback()


# --- SỬA LẠI PHẦN CHẠY THỬ (MAIN) ĐỂ KIỂM TRA LUỒNG TẢI DỮ LIỆU ---
if __name__ == "__main__":
    import pandas as pd
    from transform import transform_forecast

    # 1. Chạy khởi tạo cấu trúc bảng trước
    init_database()

    # 2. Giả lập một gói dữ liệu thành phố Hà Nội để đồng bộ bảng Dimension
    # Id 1581130 chính là mã ID thực tế của Hà Nội trả về trong file JSON của bạn
    hanoi_meta = {
        "id": 1581130,
        "name": "Hanoi",
        "country": "Vietnam",
        "latitude": 21.0245,
        "longitude": 105.84117,
        "timezone": "Asia/Bangkok",
    }

    connection = get_db_connection()
    if connection:
        # Kiểm tra nạp bảng thành phố
        insert_city(connection, hanoi_meta)

        # 3. Đọc thử bảng dữ liệu forecast sạch từ file CSV mà Pandas vừa xuất ra ở lượt chat trước
        print("\n🚚 Đang thử nghiệm nạp bảng dữ liệu forecast_clean_hanoi.csv vào Postgres...")
        try:
            df_test = pd.read_csv("data/processed/forecast_clean_hanoi.csv")
            # Vì đọc từ CSV nên cần ép lại kiểu DateTime cho cột thời gian
            df_test["measured_at"] = pd.to_datetime(df_test["measured_at"])

            # Kích hoạt hàm nạp dữ liệu hàng loạt
            insert_weather_dataframe(connection, df_test)
        except FileNotFoundError:
            print(
                "❌ Không tìm thấy file 'data/processed/forecast_clean_hanoi.csv'. Hãy chạy file 'transform.py' trước!"
            )

        connection.close()


