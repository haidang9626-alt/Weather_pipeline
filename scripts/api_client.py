from datetime import datetime
import json
import os
import requests
from dotenv import load_dotenv
import logging

load_dotenv()

api_url = os.getenv("OM_api")
os.makedirs("data/raw", exist_ok=True)
logger = logging.getLogger("Extract")

def get_toado(tentp):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": tentp, "count": 10}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as http_er:
        logger.error(f"Lỗi http từ server (có thể sai api hoặc url): {http_er}")
        return None
    except requests.exceptions.Timeout as timeout_er:
        logger.error(f"Lỗi quá thời gian chờ: {timeout_er}")
        return None
    except requests.exceptions.RequestException as RE:
        logger.error(f"Lỗi hệ thống mạng không xác định: {RE}")
        return None


def get_thoitiet(vido, kinhdo, mui_gio):
    params = {
        "latitude": vido,
        "longitude": kinhdo,
        "hourly": "temperature_2m,apparent_temperature,precipitation,surface_pressure,relative_humidity_2m,cloud_cover",
        "timezone": mui_gio,
    }
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        sodong = len(data["hourly"]["time"])
        logger.info(f"Số Dòng: {sodong}")
        return data
    
    except requests.exceptions.HTTPError as http_er:
        logger.error(f"Lỗi http từ server(sai api hoặc url): {http_er}")
        return None
    except requests.exceptions.Timeout as timeout_er:
        logger.error(f"Lỗi quá thời gian chờ (Timeout): {timeout_er}")
        return None
    except requests.exceptions.ConnectionError as conec_er:
        logger.error(f"Lỗi kết nối mạng (Connection Error): {conec_er}")
        return None
    except requests.exceptions.RequestException as RE:
        logger.error(f"Lỗi hệ thống mạng không xác định: {RE}")
        return None


def run_extract(vido, kinhdo, mui_gio, tenfile, city_id):
    forecast_raw = get_thoitiet(vido, kinhdo, mui_gio)
    
    if forecast_raw:
        now = datetime.now()
        forecast_raw["metadata"] = {
            "timestamp": int(now.timestamp()),
            "measured_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "city_id": city_id,
        }
        
        filepath = f"data/raw/forecast_raw_{tenfile}.json"
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(forecast_raw, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Lưu thành công file raw cho tỉnh: {tenfile}")
        return filepath
        
    return None


if __name__ == "__main__":
    tentp = input("Nhập tên thành phố: ")

    data = get_toado(tentp)
    ds_tp = []

    if data and "results" in data:
        ds_tp = data.get("results")
        print(f"Tìm thấy {len(ds_tp)} thành phố phù hợp\n")

    if len(ds_tp) > 0:
        for i, d in enumerate(ds_tp):
            ten = d["name"]
            quocgia = d.get("country", "Không rõ")
            tinh = d.get("admin1", "")
            quan = d.get("admin2", "")
            phuong = d.get("admin3", "")
            l = []
            if phuong:
                l.append(phuong)
            if quan:
                l.append(quan)
            if tinh:
                l.append(tinh)
            diachi = ", ".join(l)

            print(f"{i+1}. {ten} | Vị trí: {diachi} | Quốc gia: {quocgia}")

        try:
            chon = int(input("\nChọn thành phố của bạn (số): ")) - 1

            if 0 <= chon < len(ds_tp):
                Tp = ds_tp[chon]

                vido = Tp["latitude"]
                kinhdo = Tp["longitude"]
                mui_gio = Tp.get("timezone", "auto")
                city_id = Tp.get("id")

                tenfile = Tp["name"].lower().replace(" ", "_")

                logger.info(
                    f"Bắt đầu kích hoạt luồng tải dữ liệu cho thành phố: {Tp['name']}"
                )

                raw_file_path = run_extract(
                    vido, kinhdo, mui_gio, tenfile, city_id
                )

                if raw_file_path:
                    print(
                        f"\n[THÀNH CÔNG] File raw được lưu tại: {raw_file_path}"
                    )

            else:
                print("Lựa chọn số thứ tự không nằm trong danh sách.")
        except ValueError as V:
            print(f"Vui lòng nhập một số nguyên hợp lệ! Chi tiết: {V}")
    else:
        print("Không tìm thấy kết quả thành phố nào.")
