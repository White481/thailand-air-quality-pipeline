# Thailand Air Quality Pipeline

An end-to-end data pipeline that collects hourly air quality readings from monitoring stations across Thailand, joins them with weather data, and models them for analysis and a dashboard.

> **Status:** early development. The project structure is in place; components are being built step by step (see [Roadmap](#roadmap)).

## Data sources

| Source | What it provides | Module |
|---|---|---|
| [Air4Thai](http://air4thai.pcd.go.th/) (Pollution Control Department) | Hourly PM2.5, PM10, O3, CO, NO2, SO2 and AQI per station | `extract/air4thai.py` |
| [Open-Meteo](https://open-meteo.com/) | Weather (temperature, humidity, wind, precipitation) at station locations | `extract/openmeteo.py` |

## Architecture

```
Air4Thai API ─┐
              ├─► extract ─► raw JSON ─► transform (parse → validate) ─► Parquet ─► dbt (staging → marts) ─► dashboard
Open-Meteo ───┘                                                                         │
                                                                                monitoring checks
```

## Project structure

```
extract/         API clients and the pipeline entry point (handler.py)
transform/       Parse raw JSON, validate data quality, write partitioned Parquet
dbt_project/     dbt models (staging, marts), snapshots (dim_station), tests, seeds
monitoring/      Freshness and data quality checks
dashboard/       Dashboard for exploring air quality trends
analyses/        Ad-hoc analysis notebooks and queries
infra/           Infrastructure configuration
tests/           Unit tests and API response fixtures
docs/            Data dictionary and incident log
.github/         CI and scheduled daily transform workflows
```

## Getting started

Requirements: Python 3.11+

```bash
git clone https://github.com/White481/thailand-air-quality-pipeline.git
cd thailand-air-quality-pipeline
make install
cp .env.example .env   # optional overrides
```

| Command | What it does |
|---|---|
| `make test` | Run the unit tests |
| `make extract` | Fetch the latest Air4Thai readings into `data/raw/air4thai/dt=YYYY-MM-DD/` (UTC fetch date) |

> **TLS note:** `air4thai.pcd.go.th` serves an incomplete certificate chain, so standard Python clients fail verification. The missing Let's Encrypt intermediates are bundled in `extract/certs/` and added to certifi's CA bundle at runtime — verification stays fully on.

## Roadmap

- [x] Extract hourly readings from Air4Thai
- [ ] Parse and flatten station readings
- [ ] Validate data quality (missing values, sentinel values, ranges)
- [ ] Write date-partitioned Parquet
- [ ] Single command to run the pipeline (`make run`)
- [ ] Extract weather data from Open-Meteo
- [ ] dbt staging and mart models, `dim_station` snapshot
- [ ] CI and scheduled runs with GitHub Actions
- [ ] Monitoring checks
- [ ] Dashboard

## Documentation

- [Data dictionary](docs/data_dictionary.md)
- [Incident log](docs/incident_log.md)
