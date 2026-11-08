# Requirements check (for you and for the viva)

## 1. The assignment text

> Build an ETL pipeline that extracts data from an API, transforms/validates it with pandas and Pydantic, loads it to a database or a file, and conduct a structured exploratory data analysis on the result. You must explain in description the choice of dataset, where you want to load the data and EDA that you are aiming to perform.

| Requirement | Where it is done |
|---|---|
| Extract data **from an API** | `extract.py`: Open-Meteo Air Quality API + Open-Meteo Historical Weather API (`requests`). Raw JSON saved in `raw/` |
| Transform with **pandas** | `transform.py`: DataFrames, merge on time, duplicates, types, gap filling, dropping incomplete rows |
| Validate with **Pydantic** | `schema.py` (rules) + `transform.py` (`validate()` checks every row; rejects go to `processed/rejected_rows.csv`) |
| Load to a **database** | `load.py`: SQLite file `lahore_air_weather.db`, table `air_weather`, written with SQLAlchemy |
| **Structured EDA** on the result | `eda.py` + `eda_notebook.ipynb`: reads the data **back from the database**, then analyses it |
| Description: dataset, destination, EDA | Submitted on the course page (matches the table below) |
| Submission links | GitHub repository + deployed web app (`web/`) |

## 2. Every claim in the submitted description

| What the description says | Where it is |
|---|---|
| Open-Meteo Air Quality API: PM2.5, PM10, NO2, O3, CO, SO2 | `config.AIR_VARS`, `extract.py` |
| Open-Meteo Weather API: temperature, humidity, wind, pressure, precipitation | `config.WEATHER_VARS`, `extract.py` |
| `requests`, raw JSON saved unchanged | `extract.py` (also retries on errors and rate limits) |
| pandas, merged on timestamp, types fixed, duplicates removed, missing values handled | `transform.py` |
| Pydantic: field types and valid ranges, invalid rows rejected | `schema.py`, `transform.py` |
| Loaded with SQLAlchemy into a relational database | `load.py` (SQLite) |
| Read back from the database for EDA | `eda.load_data()` and the SQL query in the notebook |
| Summary statistics, missing-value checks | `outputs/summary_stats.csv`, `outputs/missing_values.csv`, notebook section 2 |
| Pollutant distributions | charts 01 and 02 |
| Hourly / daily / monthly patterns | charts 03 (hour), 04 (daily), 05 (monthly) |
| Correlation between weather variables and pollutants | chart 06 (all 6 pollutants x 5 weather variables) and 07 |
| Days above the WHO guideline | chart 08 and `outputs/daily_pm_vs_who.csv` |
| matplotlib / seaborn charts | `eda.py` (seaborn on top of matplotlib) |
| Written summary of findings | `outputs/findings.md` and the report |
| Deliverables: source code, database, EDA notebook, short report | the repository, `lahore_air_weather.db`, `eda_notebook.ipynb`, `report.docx` (made by `make_report.py`) |
| Tools: Git | GitHub repository |

## 3. Be honest about these three points if asked

- **Database:** the description says "SQLite/PostgreSQL". We load into **SQLite**. PostgreSQL would need only a different connection string in `load.py` (plus a driver), but we did not build or test it.
- **Date range:** the description says "a fixed date range". After we added the daily auto-refresh, the range is a **rolling 365 days** by default. To pin dates, set the `START_DATE` and `END_DATE` environment variables. Present the auto-refresh as an extension.
- **Air quality data is modeled** (CAMS via Open-Meteo), not measured by ground sensors. This is stated as a limitation in the report and on the website.

## 4. Before you submit

1. `python run_all.py`, then check that `outputs/` has 8 charts and `findings.md`.
2. `pip install python-docx`, then `python make_report.py --web-url https://YOUR-LINK.vercel.app`, and open `report.docx`.
3. Read the report once. The work-division table at the end is copied from the description, so edit it if your split was different.
4. Fill in "Who did what" in `VIVA_NOTES.md`.
