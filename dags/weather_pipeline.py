import sys
import os
from datetime import datetime
import joblib
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler

# Giúp Python tìm thấy các file trong thư mục scripts và ml_core [b0.1.3]
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.api_client import get_thoitiet
from scripts.transform import clean_hourly_dataframe
from scripts.data_loader import get_db_connection, insert_weather_dataframe

# Cấu hình thông tin mặc định cho Hà Nội để chạy ngầm hằng giờ [b0.1.2]
HANOI_LAT = 21.0245
HANOI_LON = 105.84117
HANOI_ID = 1581130 
HANOI_TZ = "Asia/Bangkok"


def run_hourly_etl_pipeline():
    thoigian_chay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n⏱️ [{thoigian_chay}] BẮT ĐẦU CHU KỲ ETL TỰ ĐỘNG HẰNG GIỜ...")
    
    # --- BƯỚC 1: EXTRACT (Cào dữ liệu thô từ mạng về) --- [b0.1.2]
    raw_json = get_thoitiet(HANOI_LAT, HANOI_LON, HANOI_TZ)
    if not raw_json:
        print("❌ Lỗi: Không lấy được dữ liệu từ API Open-Meteo.")
        return
        
    # --- BƯỚC 2: TRANSFORM (Dùng Pandas làm sạch và xếp thành dạng bảng) --- [b0.1.2, b0.1.10]
    df_clean = clean_hourly_dataframe(raw_json)
    if df_clean is None or df_clean.empty:
        print("❌ Lỗi: Dữ liệu API trả về bị lỗi cấu trúc.")
        return
        
    # Thêm thông tin thành phố và thời gian để lát nữa nạp vào AI học [b0.1.2]
    df_clean["city_id"] = HANOI_ID
    df_clean["hour"] = df_clean["measured_at"].dt.hour
    df_clean["month"] = df_clean["measured_at"].dt.month
    
    # --- BƯỚC 3: AI PREDICT (Gọi mô hình AI ra để dự đoán nhiệt độ) --- [b0.1.18]
    model_path = "ml_core/saved_models/weather_model.pkl"
    if os.path.exists(model_path):
        try:
            # Tải file bộ não AI lên bộ nhớ [b0.1.18]
            model = joblib.load(model_path)
            
            # Chọn đúng các cột đầu vào giống hệt như lúc Train AI
            cac_cot_dau_vao = ["humidity", "pressure", "clouds", "rain", "hour", "month"]
            
            # Bắt con AI đoán nhiệt độ dựa trên độ ẩm, áp suất hiện tại [b0.1.18]
            df_clean["predicted_temperature"] = model.predict(df_clean[cac_cot_dau_vao])
            print("🧠 AI đã tính toán và dự đoán xong nhiệt độ!")
        except Exception as e:
            print(f"⚠️ Có lỗi khi bắt AI dự đoán: {e}. Bỏ qua cột dự đoán.")
            df_clean["predicted_temperature"] = None
    else:
        print("⚠️ Cảnh báo: Không tìm thấy file bộ não AI. Cột dự đoán sẽ bị trống.")
        df_clean["predicted_temperature"] = None

    # --- BƯỚC 4: LOAD (Đổ toàn bộ dữ liệu sạch vào Database) --- [b0.1.2, b0.1.6]
    conn = get_db_connection()
    if conn:
        # Lưu bảng dữ liệu cuối cùng vào PostgreSQL chạy trong Docker [b0.1.2, b0.1.7]
        insert_weather_dataframe(conn, df_clean)
        conn.close()
        print("🏁 CHU KỲ ETL HOÀN THÀNH! Dữ liệu đã nằm an toàn trong PostgreSQL.")
    else:
        print("❌ Lỗi: Không thể kết nối cơ sở dữ liệu PostgreSQL. Hãy bật Docker Desktop!")


if __name__ == "__main__":
    # 1. Chạy thử luôn 1 lần đầu tiên khi vừa bật file lên [b0.1.9]
    run_hourly_etl_pipeline()
    
    # 2. Cài đặt trình lập lịch tự động hằng giờ [b0.1.3, b0.1.9]
    scheduler = BlockingScheduler()
    
    # Cấu hình: Cứ đúng 1 giờ (hours=1) hệ thống sẽ tự động gọi lại hàm chạy pipeline [b0.1.9]
    scheduler.add_job(run_hourly_etl_pipeline, 'interval', hours=1)
    
    print("\n📅 Hệ thống chạy ngầm đã bật thành công. Cứ mỗi 60 phút sẽ tự động cào dữ liệu mới.")
    print("👉 Vui lòng giữ nguyên Terminal này, không tắt đi.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Hệ thống tự động chạy ngầm hằng giờ đã dừng.")
