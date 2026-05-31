import os
import logging
import pandas as pd
from sqlalchemy import create_engine, MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("Load")


def upsert_df(df, engine, table_name):
    """Trùng mốc giờ thì UPDATE đè số liệu mới, chưa có thì INSERT."""
    meta = MetaData()
    meta.reflect(bind=engine)

    if table_name not in meta.tables:
        print(f" Bảng '{table_name}' không tồn tại trong database!")
        return False

    table = meta.tables[table_name]
    records = df.to_dict(orient="records")

    # Tạo câu lệnh cấu hình nạp chồng dữ liệu
    stmt = pg_insert(table).values(records)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_city_time",  
        set_={
            col: stmt.excluded[col]
            for col in df.columns
            if col not in ["city_id", "measured_at"]  # Giữ nguyên mốc giờ và ID, chỉ cập nhật số liệu
        },
    )

    with engine.begin() as conn:
        conn.execute(stmt)
    return True


def load_csv_to_db(csv_path, table_name="weather_hourly"):
    if not os.path.exists(csv_path):
        print(f" Không tìm thấy file CSV: {csv_path}")
        return False

    try:
        # 1. Đọc và chuẩn hóa dữ liệu đầu vào từ CSV
        df = pd.read_csv(csv_path)
        df["measured_at"] = pd.to_datetime(df["measured_at"])
        df["rain_tier"] = df["rain_tier"].astype(str)
        
        
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST", "localhost")

        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"
        engine = create_engine(connection_string)

        # 3. KÍCH HOẠT HÀM UPSERT  CHẶN LỖI TRÙNG KHÓA
        success = upsert_df(df, engine, table_name)
        if success:
            print(f"[Load] Đã UPSERT thành công {len(df)} dòng vào Database PostgreSQL!")
        return success

    except Exception as e:
        print(f" Lỗi tại tầng Load: {e}")
        return False


if __name__ == "__main__":
    test_csv_path = "data/processed/weather_clean_tay_ninh.csv"
    print(f"Đang nạp dữ liệu từ file: {test_csv_path}")
    # GỌI ĐÚNG HÀM ĐIỀU PHỐI ĐỂ KÍCH HOẠT UPSERT
    load_csv_to_db(test_csv_path, table_name="weather_hourly")
