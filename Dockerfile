    # 1. Sử dụng hệ điều hành Python 
    FROM python:3.10-slim

    # 2. Tạo /app chứa code
    WORKDIR /app

    # 3. Copy file danh sách thư viện
    COPY requirements.txt .

    # 4. Cài các thư viện
    RUN pip install --no-cache-dir -r requirements.txt

    # 5. Copy source code vào máy ảo
    COPY . .

    # 6. Lệnh kích hoạt: Khi container bật lên tự chạy file load
    CMD ["python", "scripts/pipeline.py"]

#docker-compose up --build
