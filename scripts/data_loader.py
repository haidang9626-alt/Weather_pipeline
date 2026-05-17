import os
from dotenv import load_dotenv
import pandas as pd
import psycopg2

load_dotenv()


def get_db_connection():
    """Hàm thiết lập kết nối tới cơ sở dữ liệu PostgreSQL trong Docker [b0.1.2, b0.1.7]."""
    try:
        conn = psycopg2.connect(
            host="localhost",
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
    """Đọc file init.sql và tự động khởi tạo cấu trúc các bảng SQL [b0.1.2, b0.1.8]."""
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
    """Chèn thông tin thành phố vào bảng danh mục 'cities' (Dimension table) [b0.1.2, b0.1.8]."""
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
    """Nạp bảng dữ liệu sạch từ Pandas (Gồm cả số thực tế và số AI đoán) vào PostgreSQL [b0.1.2, b0.1.6, b0.1.18]."""
    if df_clean is None or df_clean.empty:
        print("⚠️ Bảng dữ liệu sạch trống rỗng, bỏ qua bước Load.")
        return

    # Câu lệnh SQL đã được cập nhật thêm cột dữ liệu thông minh của AI [b0.1.2, b0.1.8]
    sql = """
    INSERT INTO weather_measurements (
        city_id, measured_at, temperature, predicted_temperature, 
        apparent_temp, rain, pressure, humidity, clouds
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (city_id, measured_at) DO UPDATE SET
        temperature = EXCLUDED.temperature,
        predicted_temperature = EXCLUDED.predicted_temperature,
        apparent_temp = EXCLUDED.apparent_temp,
        rain = EXCLUDED.rain,
        pressure = EXCLUDED.pressure,
        humidity = EXCLUDED.humidity,
        clouds = EXCLUDED.clouds;
    """

    try:
        cursor = conn.cursor()
        count = 0

        for _, row in df_clean.iterrows():
            if pd.isna(row["city_id"]):
                continue

            # Kiểm tra an toàn xem cột predicted_temperature có tồn tại trong bảng không [b0.1.18]
            val_predicted_temp = (
                row["predicted_temperature"]
                if "predicted_temperature" in row
                and not pd.isna(row["predicted_temperature"])
                else None
            )

            cursor.execute(
                sql,
                (
                    int(row["city_id"]),
                    row["measured_at"].to_pydatetime(),
                    row["temperature"] if not pd.isna(row["temperature"]) else None,
                    val_predicted_temp,  # Số liệu dự đoán hiệu chỉnh từ bộ não AI [b0.1.18]
                    row["apparent_temp"] if not pd.isna(row["apparent_temp"]) else None,
                    row["rain"] if not pd.isna(row["rain"]) else None,
                    row["pressure"] if not pd.isna(row["pressure"]) else None,
                    int(row["humidity"]) if not pd.isna(row["humidity"]) else None,
                    int(row["clouds"]) if not pd.isna(row["clouds"]) else None,
                ),
            )
            count += 1

        conn.commit()
        cursor.close()
        print(f"✔️ Đã nạp thành công {count} dòng dữ liệu (Thực tế + AI Dự đoán) vào PostgreSQL!")
    except Exception as e:
        print(f"❌ Lỗi khi nạp dữ liệu DataFrame vào DB: {e}")
        conn.rollback()


# --- PHẦN CHẠY THỬ NGHIỆM ĐỂ KIỂM TRA LUỒNG TẢI DỮ LIỆU ---
if __name__ == "__main__":
    # 1. Chạy khởi tạo cấu trúc bảng trước
    init_database()

    # 2. Tạo gói thông tin mẫu của Hà Nội để nạp vào bảng Dimension
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
        insert_city(connection, hanoi_meta)

        # 3. Đọc thử bảng dữ liệu forecast sạch từ file CSV mà bạn đã biến đổi ở bước trước
        print("\n🚚 Đang kiểm tra nạp dữ liệu sạch từ tệp CSV vào Postgres...")
        try:
            df_test = pd.read_csv("data/processed/forecast_clean_hanoi.csv")
            df_test["measured_at"] = pd.to_datetime(df_test["measured_at"])

            # Thử nghiệm nạp dữ liệu hàng loạt vào Database [b0.1.2]
            insert_weather_dataframe(connection, df_test)
        except FileNotFoundError:
            print("⚠️ Chưa tìm thấy tệp 'data/processed/forecast_clean_hanoi.csv'. Hãy chạy tệp 'transform.py' trước!")

        connection.close()
