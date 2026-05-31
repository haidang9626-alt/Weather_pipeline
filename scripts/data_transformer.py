import json
import logging
import os
import pandas as pd

logger = logging.getLogger("Transform")


def clean_and_merge(raw_json, tenfile):
    if "hourly" not in raw_json:
        logger.error(f" File dữ liệu {tenfile} không chứa mục 'hourly'!")
        return None
#trải phẳng json
    df = pd.DataFrame(raw_json["hourly"])
    before_count = len(df)

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

    df = df.drop_duplicates(subset=["measured_at"])

#chuyển kiểu dữ liệu
    df["measured_at"] = pd.to_datetime(df["measured_at"])
    df["temperature"] = df["temperature"].astype(float)
    df["apparent_temp"] = df["apparent_temp"].astype(float)
    df["rain"] = df["rain"].astype(float)
    df["pressure"] = df["pressure"].astype(float)
    df["humidity"] = df["humidity"].astype(int)
    df["clouds"] = df["clouds"].astype(int)

    # Xử lý giá trị âm 
    am_values = df[
        (df["rain"] < 0) | (df["pressure"] < 0) | (df["humidity"] < 0) | (df["clouds"] < 0)
    ]
    if not am_values.empty:
        logger.warning(
            f" Tỉnh {tenfile}: {len(am_values)} dòng có giá trị âm bất hợp lệ!"
        )
    df["rain"] = df["rain"].clip(lower=0)
    df["humidity"] = df["humidity"].clip(lower=0, upper=100)
    df["clouds"] = df["clouds"].clip(lower=0, upper=100)
    df["pressure"] = df["pressure"].clip(lower=800, upper=1100)
    
    # • Xử lý missing bằng nội suy tuyến tính
    df = df.interpolate(method="linear")

    # Sau nội suy vẫn trống điền med
    for col in [
        "temperature",
        "apparent_temp",
        "rain",
        "pressure",
        "humidity",
        "clouds",
    ]:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    df["city_id"] = raw_json.get("metadata", {}).get("city_id", None)
    df["city_name"] = tenfile.replace("_", " ").title().strip()

#chênh lệch cảm nhận và thực tế
    df["temp_diff"] = df["apparent_temp"] - df["temperature"]

    # • rain_tier: Phân loại mức độ mưa theo ngưỡng (Tương đương revenue_tier)
    bins = [-1, 0.1, 2.0, float("inf")]
    labels = ["Không mưa", "Mưa nhỏ", "Mưa to"]
    df["rain_tier"] = pd.cut(df["rain"], bins=bins, labels=labels)

    # In thông tin bản ghi trước/sau xử lý 
    after_count = len(df)
    logger.info(
        f"Transform [{df['city_name'].iloc[0]}] -> Trước: {before_count} dòng | Sau: {after_count} dòng"
    )
    return df


def transform_forecast_pipeline(raw_file_path, tenfile):
    if not os.path.exists(raw_file_path):
        logger.error(f" Không tìm thấy file thô tại đường dẫn: {raw_file_path}")
        return None

    with open(raw_file_path, "r", encoding="utf-8") as f:
        raw_json = json.load(f)

    df_clean = clean_and_merge(raw_json, tenfile)

    if df_clean is not None:
        os.makedirs("data/processed", exist_ok=True)
        output_path = f"data/processed/weather_clean_{tenfile}.csv"

        df_clean.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"Xuất file gộp chung thành công tại: {output_path}")
        return output_path

    return None



if __name__ == "__main__":

    test_file = "data/raw/forecast_raw_tay_ninh.json"
    print(f" Gộp dữ liệu cho file: {test_file}\n")

    result = transform_forecast_pipeline(test_file, "tay_ninh")
    if result:
        print(f"\n File CSV tại: {result}")
