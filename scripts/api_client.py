from datetime import datetime, timedelta
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_url_his = os.getenv("OMH_url")
api_url = os.getenv("OM_api")


def get_toado(tentp):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": tentp, "count": 10}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_er:
        print(f"Lỗi http từ server(có thể sai api hoặc url): {http_er}")
        return None
    except requests.exceptions.Timeout as timeout_er:
        print(f"Lỗi quá thời gian chờ: {timeout_er}")
        return None
    except requests.exceptions.RequestException as RE:
        print(f"Lỗi hệ thống mạng không xác định: {RE}")
        return None


def get_thoitiet(vido, kinhdo, mui_gio):
    params = {
        "latitude": vido,
        "longitude": kinhdo,
        "current": "temperature_2m,precipitation,surface_pressure",
        "hourly": "temperature_2m,apparent_temperature,precipitation,surface_pressure,relative_humidity_2m,cloud_cover",
        "timezone": mui_gio,
    }
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_er:
        print(f"Lỗi http từ server(có thể sai api hoặc url): {http_er}")
        return None
    except requests.exceptions.Timeout as timeout_er:
        print(f"Lỗi quá thời gian chờ: {timeout_er}")
        return None
    except requests.exceptions.ConnectionError as conec_er:
        print(f"Lỗi quá thời gian chờ: {conec_er}")
        return None
    except requests.exceptions.RequestException as RE:
        print(f"Lỗi hệ thống mạng không xác định: {RE}")
        return None


def get_lichsu(vido, kinhdo, mui_gio, start, end):
    params = {
        "latitude": vido,
        "longitude": kinhdo,
        "start_date": start,
        "end_date": end,
        "hourly": "temperature_2m,apparent_temperature,precipitation,surface_pressure,relative_humidity_2m,cloud_cover",
        "daily": "precipitation_hours,weather_code,temperature_2m_max,temperature_2m_min,shortwave_radiation_sum",
        "timezone": mui_gio,
    }
    try:
        response = requests.get(api_url_his, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as RE:
        print(f"Lỗi hệ thống mạng không xác định {RE}")
        return None
    except (KeyError, ValueError) as data_er:
        print(f"Lỗi cấu trúc dl json bị trống hoặc thay đổi {data_er}")
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

            print(f"{i+1} {ten} Vị trí: {diachi}, Quốc gia: {quocgia}")

        try:
            chon = int(input("\nChọn thành phố của bạn: ")) - 1

            # Sửa điều kiện so sánh nghiêm ngặt < len để tránh IndexError
            if 0 <= chon < len(ds_tp):
                Tp = ds_tp[chon]

                # Sửa cú pháp ngoặc vuông lấy dữ liệu tọa độ
                vido = Tp["latitude"]
                kinhdo = Tp["longitude"]
                mui_gio = Tp.get("timezone", "auto")

                now = datetime.now()
                timestamp = int(now.timestamp())
                thoigian_now = now.strftime("%Y-%m-%d %H:%M:%S")

                # Sửa 'day' thành 'days' cho đúng chuẩn timedelta [b0.1.2]
                homqua = now - timedelta(days=1)
                end = homqua.strftime("%Y-%m-%d")
                start = (homqua - timedelta(days=365)).strftime("%Y-%m-%d")

                tenfile = Tp["name"].lower().replace(" ", "_")

                # --- 1. XỬ LÝ LƯU FORECAST --- [b0.1.2]
                forecast_raw = get_thoitiet(vido, kinhdo, mui_gio)
                if forecast_raw:
                    forecast_raw["metadata"] = {
                        "timestamp": timestamp,
                        "measured_at": thoigian_now,
                        "city_id": Tp.get("id"),
                    }
                    with open(
                        f"forecast_raw_{tenfile}.json", "w", encoding="utf-8"
                    ) as f:
                        json.dump(forecast_raw, f, indent=4, ensure_ascii=False)
                    print(f"Lưu thành công file raw forecast của {tenfile}")

                # --- 2. XỬ LÝ LƯU HISTORY --- [b0.1.2]
                print(
                    f" Đang cào dữ liệu lịch sử từ {start} đến {end}, vui lòng đợi..."
                )
                his_raw = get_lichsu(vido, kinhdo, mui_gio, start, end)
                if his_raw:
                    # Bổ sung dấu phẩy ngăn cách các tham số trong open()
                    with open(
                        f"history_raw_{tenfile}.json", "w", encoding="utf-8"
                    ) as f:
                        json.dump(his_raw, f, indent=4, ensure_ascii=False)
                    print(f"Lưu thành công file raw history của {tenfile}")

            else:
                print("Lựa chọn số thứ tự không nằm trong danh sách.")
        except ValueError as V:
            print(f"Vui lòng nhập một số nguyên hợp lệ! Chi tiết: {V}")
    else:
        print("Không tìm thấy kết quả thành phố nào.")
