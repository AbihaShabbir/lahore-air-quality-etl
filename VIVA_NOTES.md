# Viva notes: how we built it (read this before the viva)

## 30-second summary
We built a pipeline that downloads hourly air quality and weather data for Lahore from the
Open-Meteo APIs, cleans and validates it, stores it in a database, and analyzes how weather
relates to pollution. A small website shows the results.

`API -> raw JSON -> pandas -> Pydantic -> SQLite -> EDA -> website`

## Likely questions and short answers

**What is ETL?** Extract (get data), Transform (clean it), Load (store it). Our order: extract.py, transform.py (+ schema.py), load.py.

**Why this dataset?** Lahore has serious smog in winter, the APIs are free with no key, and air quality and weather share timestamps, so they can be merged.

**Why two APIs?** Open-Meteo has separate services for air quality and weather. We merge them on the `time` column. Both calls use the same timezone (Asia/Karachi) so hours line up.

**What does extract.py do if the API fails?** It retries up to 4 times, waits when rate-limited (error 429), and stops with a clear message if no data comes back. It saves the raw JSON unchanged so we can re-run later without calling the API again.

**What cleaning did you do in pandas?** Merged the tables, removed duplicate timestamps, converted columns to numbers, filled gaps of up to 3 hours by linear interpolation, and dropped rows still missing PM2.5, PM10 or any weather value.

**Why only fill gaps up to 3 hours?** A short sensor gap can be estimated safely. Inventing many hours would put fake data into the analysis.

**What does Pydantic add if pandas already cleaned the data?** pandas cleans; Pydantic *checks the rules* row by row (humidity must be 0-100, PM2.5 cannot be negative, pressure 850-1100 hPa and so on). Rows that break a rule go to `processed/rejected_rows.csv` with the reason instead of silently entering the database.

**Why are there 0 rejected rows?** The real data was already clean, so no row broke a rule. That is a valid result. (To demonstrate rejection, run the demo below.)

**Why SQLite?** It is a real SQL database stored in one file, with no server to install. We write with SQLAlchemy (falls back to Python's built-in sqlite3). It could be switched to PostgreSQL by changing the connection string in `load.py` (and installing a PostgreSQL driver).

**How does the EDA read the data?** From the database (`eda.load_data()`), not from the CSV. That shows the Load step really worked.

**What is the WHO guideline you compare with?** WHO 2021 24-hour guideline: PM2.5 15 and PM10 45 ug/m3. A day counts only if it has at least 18 hourly readings.

**What did you find?** See `outputs/findings.md` and the website: winter is much worse than the rest of the year, pollution peaks at night and early morning, and lower temperature and higher humidity go with higher PM2.5. Say "associated with", not "causes".

**What are the limitations?** The air quality numbers are modeled (CAMS), not measured by sensors in Lahore; one grid point represents the whole city; correlation is not causation.

**How does the website get its data?** `export_web_data.py` summarizes the database into `web/data.js`. `web/index.html` + `app.js` draw the charts in the browser (we wrote the SVG chart code ourselves, no library). It is a static site hosted on Vercel, so there is no server or database online.

**How does the project update itself?** A scheduled GitHub Actions job (`.github/workflows/refresh.yml`) runs `run_all.py` once a day at 02:30 UTC. `config.py` uses a rolling window (the last 365 days, ending 6 days ago because the weather archive lags about 5 days). The job commits the new `web/data.js` and `findings.md`, and Vercel redeploys the site. It is a daily batch job, not real-time. If any stage fails, nothing is committed, so the site keeps the last good data.

**How would you improve it?** Add more years, add ground-station data (for example from AirNow/PurpleAir) to compare with the model, or use the cleaned data as the input for the next course project (the scikit-learn pipeline).

## Demo: show that validation catches bad data (optional, ~1 minute)
This uses FAKE data in a separate folder, so your real project is not touched. In the VS Code terminal (PowerShell), inside the project folder:

```
$env:ETL_BASE = "C:\temp\demo"
python tests/make_sample_data.py
python run_all.py --skip-extract
Remove-Item Env:ETL_BASE
```

Then open `C:\temp\demo\processed\rejected_rows.csv`: it shows 2 rows rejected (humidity 140, temperature 90) and the reason. The sample data also has a duplicate hour and a 20-hour gap, which the transform step fixes or drops (see `transform_report.json`).

## Who did what (fill in)
- 2025-AI-254:
- 2025-AI-255:
- 2025-AI-260:
