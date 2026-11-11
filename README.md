# Campus Digital Twin — Smart Campus Analytics

A beginner-friendly, mobile-first campus occupancy prototype built with Flask, Pandas, NumPy, SQLite, HTML, CSS, vanilla JavaScript, and Plotly.js. It demonstrates CSV cleaning, historical analysis, JSON APIs, and data visualization using **synthetic demonstration data only**.

> **Data honesty:** The included records are generated sample data for the fixed dates October 12–18, 2026. This app does not collect live student counts, connect to campus sensors, or use satellite imagery to estimate people inside buildings. Its campus diagram is illustrative, not geographic.
>
> **Public deployment status:** This repository contains a Render deployment blueprint, but a public URL is not created until an owner connects a GitHub repository and approves the hosting resources in their Render account.

## Project structure

```text
Campus-Digital-Twin/
├── app.py
├── generate_dataset.py
├── requirements.txt
├── README.md
├── render.yaml
├── .gitignore
├── analysis/
│   ├── __init__.py
│   └── analytics.py
├── database/
│   ├── __init__.py
│   └── db.py                 # SQLite locally; PostgreSQL when DATABASE_URL is set
├── data/
│   ├── campus.csv
│   ├── crowd.csv
│   ├── library.csv
│   ├── labs.csv
│   ├── canteen.csv
│   └── parking.csv
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── favicon.svg
└── tests/
    └── test_api.py
```

## Run on Windows / VS Code

Open this project folder in VS Code, then run these commands in its PowerShell terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python generate_dataset.py
python app.py
```

**Important:** Do not double-click an HTML file or use VS Code's Live Server for this project. The dashboard needs Flask to serve the page and its `/api/...` data. The correct page is served from `frontend/index.html` when Flask is running; `Untitled-1.html` is an older standalone prototype.

If PowerShell blocks virtual-environment activation, use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe generate_dataset.py
.\.venv\Scripts\python.exe app.py
```

Leave the terminal open while the server is running, then open <http://127.0.0.1:5000/> in Chrome. SQLite is seeded once from the CSV files locally and is not recreated on every restart. The charts use Plotly.js from its free CDN, so chart rendering needs an internet connection; the Flask API and sample data are local. Press `Ctrl+C` in the terminal to stop the server.

### Re-create the sample files

`generate_dataset.py` uses a fixed random seed and a fixed seven-day date range. Every generated CSV row includes a `data_label` column set to `SYNTHETIC DEMONSTRATION DATA`. To write the same files to another directory:

```powershell
python generate_dataset.py --output-dir .\data
```

The generated campus coordinates are intentionally blank. The map in the interface uses a custom illustrative layout and must not be treated as actual campus geography.

## Tests

```powershell
python -m pytest -q
```

The tests cover occupancy calculation and status-threshold boundaries, missing/non-finite data, required CSV columns, reproducible sample shape and derived availability, SQLite persistence, API response shapes and empty ranges, date/time/facility/category filters, invalid requests, configurable thresholds, and frontend/API route consistency.

## Public HTTPS deployment (Render + GitHub)

The app and API are served from one origin, so the browser uses the relative `/api/...` paths. **CORS is intentionally not enabled:** there is no separate API domain to authorize, and wildcard CORS would add exposure without benefit.

`render.yaml` defines a Render Python web service, a persistent PostgreSQL database, and `/healthz` as the service health check. `DATABASE_URL` is supplied by Render; SQLAlchemy uses the PostgreSQL driver in deployment and SQLite for local development. The example database is seeded once. A restart or redeploy will not replace existing database rows with CSV data. New seed versions require an intentional version change in `database/db.py`.

The included `.github/workflows/tests.yml` runs the API/data tests for pushes and pull requests. The Render blueprint sets automatic deployment to wait until GitHub checks pass. Test the live health endpoint at `https://YOUR-SERVICE.onrender.com/healthz`; Render assigns the exact HTTPS URL after the first successful deployment.

### One-time steps that require your accounts

This workspace does not have Git installed, is not a Git repository, and has no GitHub or Render credentials. I cannot create a provider account, connect OAuth, approve billing, push your project, or truthfully provide a public URL without those owner-controlled actions.

1. Create/sign in to [GitHub](https://github.com/) and [Render](https://render.com/). Keep the source repository **private** if you do not want the source code public; a private repo can still deploy to a public website.
2. Install [Git for Windows](https://git-scm.com/download/win) if it is not installed. In the project folder, use VS Code's Source Control view to initialize a repository, commit the project, create a private GitHub repository, and push it. The `.gitignore` excludes your local `.venv`, environment files, and SQLite database.
3. In Render, choose **New → Blueprint**, connect GitHub, and select that repository. Review the `campus-digital-twin` web service and `campus-digital-twin-db` PostgreSQL resources defined in `render.yaml`.
4. The blueprint specifies paid `starter` web compute and `basic-256mb` PostgreSQL storage so the service does not sleep and application data persists. Render shows the current charges before provisioning; approve only if they fit your budget. You do not need to enter any API key in the source files.
5. Wait for the deployment to report **Live**, then open the HTTPS URL Render shows. Confirm `/healthz` returns `{"status":"ok","database":"ok"}` and the dashboard loads data. Future pushes to the linked branch run tests on GitHub and trigger Render's automatic deployment.

Do not post database credentials or private keys in chat, GitHub files, or screenshots. If the deployment fails, share the non-secret build/runtime error text and I can help diagnose it.

### Free-tier trade-offs

Render documents that a free web service spins down after 15 minutes without inbound traffic and can take about a minute to wake. Its filesystem is ephemeral, so local SQLite is not durable there. Render's free Postgres is limited to 1 GB and expires after 30 days (with a 14-day upgrade grace period), and it has no backups. Render also currently grants 750 free instance hours per workspace each calendar month; exceeding the allowance suspends free web services until the next month. These limits are unsuitable for a durable public site, which is why the included blueprint chooses paid plans. Check [Render's current pricing](https://render.com/pricing) before approving; provider prices and plan availability can change.

### Production configuration

- `DATABASE_URL`: Render's managed PostgreSQL connection string; never commit its value.
- `PORT`: Render supplies the listening port to its process manager. The deployed service runs Gunicorn, not Flask's development server.
- `OCCUPANCY_MODERATE_THRESHOLD` and `OCCUPANCY_HIGH_THRESHOLD`: optional numeric overrides; defaults are 70 and 85.
- `/healthz`: checks that the database connection works and returns HTTP 503 if it does not.
- Gunicorn access and error logs are written to standard output/error for Render's log viewer.
- TLS termination is handled by Render; the app honors the provider's forwarded HTTPS scheme and sends basic security headers.

## API

All endpoints return JSON. Errors use the shape `{"error":{"code":"...","message":"..."}}`.

| Method and route | Purpose |
| --- | --- |
| `GET /api/overview` | Filter-aware summary and current selected-sample facility indicators |
| `GET /api/facilities` | Facility occupancy and capacity summaries |
| `GET /api/facility/<location_id>` | Facility detail and historical trend |
| `GET /api/crowd` | People-count observations (parking spaces are excluded from people counts) |
| `GET /api/analytics` | Trend, hourly/daily patterns, utilization, and capacity comparisons |
| `GET /api/insights` | Recommendations derived from selected records |
| `GET /api/notifications` | High-occupancy and informational sample alerts |

Supported query parameters are `start_date=YYYY-MM-DD`, `end_date=YYYY-MM-DD`, `period=all|morning|afternoon|evening`, `facility=<building_id>|all`, and `category=all|crowd|library|laboratory|canteen|parking`. Date bounds are inclusive. Morning covers 06:00–11:59, afternoon 12:00–16:59, and evening 17:00–23:59. Invalid dates, ranges, filters, and unknown facilities return a clear client error.

Default occupancy status thresholds are set in `analysis/analytics.py`: below 70% is comfortable, 70–84.9% is moderate, and 85% or higher is high. They can be overridden when creating the Flask app, for example with `create_app({"OCCUPANCY_THRESHOLDS": {"moderate": 65, "high": 80}})`; the map, facility cards, insights, and chart colors use the API-provided values. A facility cannot exceed its capacity in valid sample data; malformed timestamps, invalid counts, and invalid capacities are removed during preprocessing.

## How data moves through the app

1. `generate_dataset.py` writes reproducible CSV records with matching campus IDs, seven days of morning/afternoon/evening samples, and derived available-seat/space columns.
2. On startup, `database/db.py` loads the CSVs into Pandas, validates columns and values, derives normalized occupancy observations, then refreshes local SQLite tables.
3. `analysis/analytics.py` applies date, time-period, facility, and category filters and calculates utilization, peaks, comparisons, and data-derived insights with Pandas and NumPy.
4. `app.py` exposes those calculations as Flask JSON endpoints. The UI labels results as synthetic historical samples; it never presents them as verified live counts.
5. `frontend/script.js` fetches the API responses and passes the returned values to Plotly.js and the facility/map cards. Changing a filter requests updated metrics and charts.

SQLite is used as a local structured cache of the validated CSV datasets, so the project remains self-contained and does not need a hosted database or paid service.
