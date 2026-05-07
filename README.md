# GridCast

Renewable generation forecasting pipeline for the DE-LU bidding zone. Predicts hourly solar, onshore wind, and offshore wind generation using weather data and compares five model architectures.

## Overview

GridCast fetches generation data from ENTSO-E and weather data from Open-Meteo, stores them in PostgreSQL, and trains ML models to forecast renewable generation. The pipeline covers:

- **Data ingestion** — ENTSO-E generation/load, Open-Meteo weather (6 inland + 1 North Sea grid point)
- **Feature engineering** — cyclical time encoding, weather features, sliding window sequences
- **Models** — Linear Regression, Random Forest, Gradient Boosting, MLP, Transformer
- **Evaluation** — RMSE, MAE, R² per target; prediction vs actual plots

## Setup

### Requirements

- Python 3.10+
- Docker (for PostgreSQL)
- ENTSO-E API key ([register here](https://transparency.entsoe.eu))

### Install

```bash
pip install -e ".[dev]"
```

### Configure

Create `.env.postgres` in the project root:

```
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=gridcast
PGHOST=localhost
PGPORT=5432
ENTSOE_API_KEY=your_entsoe_api_key
```

### Start the database

Requires Docker to be running. On macOS with Colima:

```bash
colima start
docker compose up -d
```

On other systems, start Docker Desktop and then:

```bash
docker compose up -d
```

### Initialize schema and views

Run the following in a notebook or Python session:

```python
from sqlalchemy import text
from ingestion.utils import engine

with engine.connect() as conn:
    conn.execute(text(open("db/schema.sql").read()))
    conn.execute(text(open("features/views.sql").read()))
    conn.commit()
```

### Ingest data

```python
from ingestion.entsoe_loader import load_entso_e
from ingestion.openmeteo_loader import load_weather
from ingestion.utils import write_to_db

for year in ["2020", "2021", "2022", "2023", "2024"]:
    df_meteo = load_weather(f"{year}-01-01", f"{year}-12-31")
    write_to_db(df_meteo, "meteo")

    frames = load_entso_e(f"{year}-01-01", f"{year}-12-31")
    for table, df in frames.items():
        write_to_db(df, table)
```

## Project Structure

```
gridcast/
├── db/                  # Schema DDL
├── features/            # SQL views
├── ingestion/           # ENTSO-E and Open-Meteo loaders
├── models/
│   ├── features.py      # Feature engineering and sequence building
│   ├── utils.py         # Data loading, scaling, prepare_data
│   ├── train.py         # sklearn models (linear, RF, GB)
│   ├── train_neural.py  # MLP with early stopping
│   ├── train_transformer.py  # Transformer encoder
│   ├── evaluate.py      # RMSE, MAE, R² metrics
│   ├── plot.py          # Prediction vs actual plots
│   └── persistence.py   # Save/load models and predictions
├── tests/               # pytest test suite
└── dashboard/           # Streamlit dashboard (in progress)
```

## Tests

```bash
pytest tests/
```

## Data Attribution

See [ATTRIBUTION.md](ATTRIBUTION.md). Raw data is not redistributed — all data is fetched at runtime using your own API credentials.

## License

MIT
