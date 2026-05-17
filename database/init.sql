def insert_weather_dataframe
(conn, df_clean):
    """
    Nhận bảng DataFrame sạch từ Pandas (đã bao gồm cột dự đoán của AI) 
    và chèn hàng loạt vào bảng 'weather_measurements' [b0.1.2, b0.1.6, b0.1.10].
    """
if df_clean is None or df_clean.
empty:
print("⚠️ Bảng dữ liệu sạch trống rỗng, bỏ qua bước Load.")
return

    #
Câu lệnh SQL bổ sung cột predicted_temperature của AI [b0.1.2, b0.1.8]
    sql = """
    INSERT INTO weather_measurements (
        city_id, measured_at, temperature, predicted_temperature, 
        apparent_temp, rain, pressure, humidity, clouds
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (city_id, measured_at) DO UPDATE SET
        temperature = EXCLUDED.temperature,
        predicted_temperature = EXCLUDED.predicted_temperature, -- Ghi đè nếu AI tính lại số mới [b0.1.18]
        apparent_temp = EXCLUDED.apparent_temp,
        rain = EXCLUDED.rain,
        pressure = EXCLUDED.pressure,
        humidity = EXCLUDED.humidity,
        clouds = EXCLUDED.clouds;
    """

try:
cursor = conn.cursor
()
        count = 0

        for _, row in df_clean.iterrows
():
if pd.isna(row["city_id"]):
continue

# Kiểm tra an toàn xem cột dữ liệu của AI có tồn tại trong bảng Pandas không [b0.1.18]
            val_predicted_temp =
(
                row["predicted_temperature"]
if "predicted_temperature" in row
                and not pd.isna
(row["predicted_temperature"])
                else None
            )

            cursor.
execute(
                sql,
(
                    int
(row["city_id"]),
                    row["measured_at"].to_pydatetime
(),
                    row["temperature"]
if not pd.isna(row["temperature"])
                    else None,
                    val_predicted_temp,  # Truyền giá trị của bộ não AI vào đây [b0.1.18]
                    row["apparent_temp"]
if not pd.isna(row["apparent_temp"])
                    else None,
                    row["rain"]
if not pd.isna(row["rain"]) else None,
                    row["pressure"]
if not pd.isna(row["pressure"]) else None,
                    int
(row["humidity"])
if not pd.isna(row["humidity"])
                    else None,
                    int
(row["clouds"])
if not pd.isna(row["clouds"]) else None,
                ),
            )
            count += 1

        conn.
commit
()
        cursor.
close
()
print(f
"✔️ Đã nạp thành công {count} dòng dữ liệu (Thực tế + AI Dự đoán) vào PostgreSQL!")
    except Exception as
e:
print(f
"❌ Lỗi khi nạp dữ liệu DataFrame vào DB: {e}")
        conn.
rollback
()
