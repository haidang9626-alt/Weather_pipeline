import sys
import os
import logging
from datetime import datetime
import joblib
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler

# Thêm thư mục gốc vào hệ thống để Python nhận diện được các thư mục con [b0.1.3]
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.api_client import get_thoitiet
from scripts.transform import clean_hourly_dataframe
from scripts.data_loader import get_db_connection, insert_weather_dataframe

# CẤU HÌNH NHẬT KÝ LOGGING CHUẨN ĐỂ CHẠY TỰ ĐỘNG NGẦM [b0.1.2]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/pipeline.log", encoding="utf-8"),  # Ghi nhật ký vào file để kiểm tra [b0.1.2]
        logging.StreamHandler()  # In ra màn hình Terminal
    ]
)
logger = logging.getLogger("WeatherPipeline")

# Cấu hình cứng tọa độ và ID của Hà Nội phục vụ chạy ngầm hằng giờ [b0.1.2]
HANOI_LAT = 21.0245
HANOI_LON = 105.84117
HANOI_ID = 1581130 
HANOI_TZ = "Asia/Bangkok"


def run_hourly_etl_pipeline():
    logger.info("⏱️ BẮT ĐẦU CHU KỲ ETL TỰ ĐỘNG HẰNG GIỜ...")
    
    # --- BƯỚC 1: EXTRACT (Cào dữ liệu dự báo thời gian thực) --- [b0.1.2]
    raw_json = get_thoitiet(HANOI_LAT, HANOI_LON, HANOI_TZ)
    if not raw_json:
        logger.error("❌ Thất bại ở bước Extract: Không gọi được API Open-Meteo.")
        return
        
    # --- BƯỚC 2: TRANSFORM (Làm sạch và phẳng hóa mảng JSON thành bảng Pandas) --- [b0.1.2, b0.1.10]
    df_clean = clean_hourly_dataframe(raw_json)
    if df_clean is None or df_clean.empty:
        logger.error("❌ Thất bại ở bước Transform: Dữ liệu JSON bị lỗi cấu trúc.")
        return
        
    # Chèn khóa ngoại city_id và tạo thêm trường mốc thời gian để đưa vào AI
    df_clean["city_id"] = HANOI_ID
    df_clean["hour"] = df_clean["measured_at"].dt.hour
    df_clean["month"] = df_clean["measured_at"].dt.month
    
    # --- BƯỚC 3: AI PREDICT (Gọi bộ não AI tính toán cột nhiệt độ thông minh) --- [b0.1.18]
    model_path = "ml_core/saved_models/weather_model.pkl"
    if os.path.exists(model_path):
        try:
            # Tải bộ não AI lên bộ nhớ [b0.1.18]
            model = joblib.load(model_path)
            
            # Khai báo đúng các cột đầu vào y hệt như lúc Train
            cac_cot_dau_vao = ["humidity", "pressure", "clouds", "rain", "hour", "month"]
            X = df_clean[cac_cot_dau_vao]
            
            # AI tính toán chớp nhoáng nhả ra mảng nhiệt độ hiệu chỉnh [b0.1.18]
            df_clean["predicted_temperature"] = model.predict(X)
            logger.info("🧠 AI đã tính toán và hiệu chỉnh nhiệt độ dự báo thành công!")
        except Exception as e:
            logger.error(f"⚠️ Lỗi khi gọi AI dự đoán: {e}. Hệ thống sẽ bỏ qua cột dự đoán.")
            df_clean["predicted_temperature"] = None
    else:
        logger.warning("⚠️ Không tìm thấy file bộ não AI, cột predicted_temperature sẽ bị trống.")
        df_clean["predicted_temperature"] = None

    # --- BƯỚC 4: LOAD (Đổ bảng dữ liệu kết hợp vào PostgreSQL) --- [b0.1.2, b0.1.6]
    conn = get_db_connection()
    if conn:
        # Trước khi lưu, sửa hàm insert_weather_dataframe ở loader để ghi nhận cột predicted_temperature
        # LƯU Ý: Để đơn giản, loader sẽ lưu bảng df_clean này vào Database
        insert_weather_dataframe(conn, df_clean)
        conn.close()
        logger.info("🏁 CHU KỲ ETL HOÀN THÀNH XUẤT SẮC! DỮ LIỆU ĐÃ NẰM TRONG POSTGRESQL.")
    else:
        logger.error("❌ Thất bại ở bước Load: Không thể kết nối cơ sở dữ liệu PostgreSQL trong Docker.")


if __name__ == "__main__":
    # Chạy ngay lập tức một lần khi vừa bật file lên để kiểm tra luồng chạy [b0.1.9]
    run_hourly_etl_pipeline()
    
    # Khởi tạo trình lập lịch chu kỳ [b0.1.3, b0.1.9]
    scheduler = BlockingScheduler()
    
    # Thiết lập tác vụ: Cứ sau đúng 1 giờ (hours=1) tự động kích hoạt lại đường ống [b0.1.9]
    scheduler.add_job(run_hourly_etl_pipeline, 'interval', hours=1)
    
    logger.info("📅 Trình chạy tự động hằng giờ đã bật ngầm thành công. Không tắt Terminal này.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Hệ thống điều phối tự động đã dừng.")
