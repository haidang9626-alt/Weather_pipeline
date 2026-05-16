import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_toado(tentp):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params={"name":tentp,
            "count":10
            }
    try :
        response= requests.get(url, params=params,timeout =10)
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


def get_thoitiet(vido,kinhdo, mui_gio):
    
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
    except requests.exceptions.ConnectionError as conec_er:
        print(f"Lỗi quá thời gian chờ: {conec_er}")
        return None
    except requests.exceptions.RequestException as RE:
        print(f"Lỗi hệ thống mạng không xác định: {RE}")
        return None


if __name__ == "__main__":
    tentp = input("Nhập tên thành phố: ")
    
    data= get_toado(tentp)
    if data and "results" in data:
        ds_tp=data.get("results")
        print(f"Tìm thấy {len(ds_tp)} thành phố phù hợp")
        
    if len(ds_tp)>1:
        for i, d in enumerate(ds_tp):
            ten= d["name"]
            quocgia= d.get("country","Không rõ")
            tinh = d.get("admin1", "")
            quan = d.get("admin2", "")
            phuong = d.get("admin3", "")
            l= []
            if phuong: l.append(phuong)
            if quan: l.append(quan)
            if tinh: l.append(tinh)
            diachi=", ".join(l)
            
            print(f"{i+1} {ten} Vị trí: {diachi}, Quốc gia: {quocgia}")
    
