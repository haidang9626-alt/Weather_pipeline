# Weather Data Pipeline (MLE Fintech Track)

## 📌 Project Overview
A Production-ready ETL pipeline that extracts weather data, transforms it using Pydantic, and loads it into a PostgreSQL Star Schema.

## 🏗️ Architecture (Kiến trúc)
- **Extract**: OpenWeatherMap API (using `requests`)
- **Transform**: Data cleaning & validation (using `pandas`, `pydantic`)
- **Load**: PostgreSQL (using `SQLAlchemy`)
- **Orchestration**: `APScheduler`
- **Infrastructure**: Docker & Docker Compose

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **Database**: PostgreSQL
- **DevOps**: Docker, GitHub Actions (CI/CD)

## 🚀 How to Run
1. Clone the repo: `git clone <your-repo-url>`
2. Setup environment: Create a `.env` file with your `API_KEY`.
3. Run with Docker: `docker-compose up --build`
# Weather_pipeline
