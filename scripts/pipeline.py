import logging
import os

from api_client import run_extract
from data_loader import load_csv_to_db
from data_transformer import transform_forecast_pipeline

# ── Logging setup ──────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("Pipeline")

CITIES = [
        {
            "name": "Tay Ninh",
            "lat": 11.3100,
            "lon": 106.0980,
            "tz": "Asia/Ho_Chi_Minh",
            "id": 1567807,
        },
        {
            "name": "Ho Chi Minh City",
            "lat": 10.8231,
            "lon": 106.6297,
            "tz": "Asia/Ho_Chi_Minh",
            "id": 1580578,
        },
    ]


def run_pipeline():
    for city in CITIES:
        slug = city["name"].lower().replace(" ", "_")
        logger.info(f"--- Bắt đầu: {city['name']} ---")

        raw_path = run_extract(city["lat"], city["lon"], city["tz"], slug, city["id"])
        if not raw_path:
            logger.error(f"Extract thất bại, bỏ qua {city['name']}")
            continue

        csv_path = transform_forecast_pipeline(raw_path, slug)
        if not csv_path:
            logger.error(f"Transform thất bại, bỏ qua {city['name']}")
            continue

        load_csv_to_db(csv_path)
        logger.info(f"Hoàn thành: {city['name']}")


if __name__ == "__main__":
    run_pipeline()
