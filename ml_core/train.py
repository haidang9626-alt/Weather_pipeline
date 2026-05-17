import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split


def huấn_luyện_ai(file_data_sạch):
    if not os.path.exists(file_data_sạch):
        print(f"❌ Không tìm thấy file dữ liệu lịch sử sạch tại: {file_data_sạch}")
        print("💡 Hãy đảm bảo bạn đã chạy file 'transform.py' trước!")
        return

    print("📖 Bước 1: Đang nạp dữ liệu lịch sử 1 năm vào bộ nhớ...")
    df = pd.read_csv(file_data_sạch)

    # Tạo thêm các đặc trưng thời gian để AI nhận diện chu kỳ ban ngày/ban đêm [b0.1.18]
    df["measured_at"] = pd.to_datetime(df["measured_at"])
    df["hour"] = df["measured_at"].dt.hour
    df["month"] = df["measured_at"].dt.month

    # 2. XÁC ĐỊNH ĐẦU VÀO VÀ ĐẦU RA CHO AI
    cac_cot_dau_vao = ["humidity", "pressure", "clouds", "rain", "hour", "month"]
    X = df[cac_cot_dau_vao]
    y = df["temperature"]

    print("✂️ Bước 2: Chia dữ liệu thành 2 tập (80% để học - 20% để kiểm tra)...")
    # Đã sửa lỗi chính tả thụt dòng (Indentation) tại đây [b0.1.2]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("🏋️ Bước 3: Thuật toán Random Forest đang rèn luyện tìm quy luật...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    print("📊 Bước 4: Đánh giá chất lượng học tập của AI...")
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    
    # Sử dụng root_mean_squared_error hoặc dùng phép tính lũy thừa thay cho tham số squared cũ của phiên bản mới [b0.1.2]
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    
    print(f"   - Sai số tuyệt đối trung bình (MAE): {mae:.2f}°C")
    print(f"   - Sai số căn bậc hai (RMSE): {rmse:.2f}°C")

    # 5. ĐÓNG GÓI BỘ NÃO AI THÀNH FILE CỨNG
    os.makedirs("ml_core/saved_models", exist_ok=True)
    file_path = "ml_core/saved_models/weather_model.pkl"
    joblib.dump(model, file_path)
    print(f"✔️ THÀNH CÔNG! Bộ não AI đã được đóng gói an toàn tại: {file_path}")


if __name__ == "__main__":
    path_lichsu_clean = "data/processed/history_clean_hanoi.csv"
    huấn_luyện_ai(path_lichsu_clean)
