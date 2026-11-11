"""Flask server for the Campus Digital Twin demonstration."""

from __future__ import annotations

from datetime import date
import os
from pathlib import Path
from typing import Any

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.middleware.proxy_fix import ProxyFix

from analysis.analytics import (
    DATA_LABEL,
    PERIOD_HOURS,
    THRESHOLDS,
    DatasetError,
    apply_filters,
    build_facilities,
    build_insights,
    status_for,
)
from database.db import initialize_database, load_analysis_frames


PROJECT_DIR = Path(__file__).resolve().parent
VALID_PERIODS = {"all", *PERIOD_HOURS}
VALID_CATEGORIES = {"all", "crowd", "library", "laboratory", "canteen", "parking"}


def _json_error(message: str, status: int, code: str) -> tuple[Any, int]:
    return jsonify({"error": {"code": code, "message": message}}), status


def _parse_date(value: str | None, parameter: str) -> date | None:
    if not value:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{parameter} must use YYYY-MM-DD format.") from error
    if parsed.isoformat() != value:
        raise ValueError(f"{parameter} must use YYYY-MM-DD format.")
    return parsed


def _filtered_observations() -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = request.environ["campus_frames"]
    start_date = _parse_date(request.args.get("start_date"), "start_date")
    end_date = _parse_date(request.args.get("end_date"), "end_date")
    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date must be on or before end_date.")
    period = request.args.get("period", "all").lower()
    category = request.args.get("category", "all").lower()
    facility_id = request.args.get("facility", "all")
    if period not in VALID_PERIODS:
        raise ValueError("period must be all, morning, afternoon, or evening.")
    if category not in VALID_CATEGORIES:
        raise ValueError("category is not supported.")
    campus = frames["campus"].copy()
    valid_facilities = set(campus["building_id"].astype(str))
    if facility_id != "all" and facility_id not in valid_facilities:
        raise ValueError("facility does not match a known campus location.")
    observations = apply_filters(
        frames["observations"],
        start_date=start_date,
        end_date=end_date,
        time_period=period,
        facility_id=facility_id,
    )
    if category != "all":
        observations = observations[observations["category"] == category].copy()
    return observations, campus


def _number(value: Any) -> int | float:
    return int(value) if float(value).is_integer() else round(float(value), 1)


def _analytics_payload(observations: pd.DataFrame) -> dict[str, Any]:
    if observations.empty:
        return {
            "summary": {
                "average_occupancy_percentage": 0,
                "peak_occupancy_percentage": 0,
                "minimum_occupancy_percentage": 0,
                "peak_hour": None,
                "average_people_count": 0,
                "maximum_people_count": 0,
                "minimum_people_count": 0,
            },
            "trend": [],
            "hourly": [],
            "daily": [],
            "facility_comparison": [],
            "capacity_comparison": [],
        }

    people = observations[observations["unit"] == "people"]
    if people.empty:
        hourly_totals = pd.DataFrame(columns=["hour", "people_count"])
        daily_totals = pd.DataFrame(columns=["date", "people_count"])
        trend = pd.DataFrame(columns=["timestamp", "people_count"])
        peak_hour = None
    else:
        trend = (
            people.groupby("timestamp", as_index=False)["occupied_count"]
            .sum()
            .rename(columns={"occupied_count": "people_count"})
        )
        hourly_totals = (
            trend.assign(hour=trend["timestamp"].dt.hour)
            .groupby("hour", as_index=False)["people_count"]
            .mean()
        )
        daily_totals = (
            trend.assign(date=trend["timestamp"].dt.strftime("%Y-%m-%d"))
            .groupby("date", as_index=False)["people_count"]
            .mean()
        )
        peak_hour = int(hourly_totals.loc[hourly_totals["people_count"].idxmax(), "hour"])

    facility_means = (
        observations.groupby(["facility_id", "facility_name", "unit"], as_index=False)
        .agg(
            average_occupancy_percentage=("occupancy_percentage", "mean"),
            capacity=("capacity", "max"),
            average_occupied=("occupied_count", "mean"),
        )
        .sort_values("average_occupancy_percentage", ascending=False)
    )
    latest = (
        observations.sort_values("timestamp")
        .groupby(["facility_id", "facility_name", "unit"], as_index=False)
        .tail(1)
    )
    latest = latest[["facility_id", "facility_name", "unit", "capacity", "occupied_count"]]
    people_counts = trend["people_count"]
    return {
        "summary": {
            "average_occupancy_percentage": round(float(observations["occupancy_percentage"].mean()), 1),
            "peak_occupancy_percentage": round(float(observations["occupancy_percentage"].max()), 1),
            "minimum_occupancy_percentage": round(float(observations["occupancy_percentage"].min()), 1),
            "peak_hour": peak_hour,
            "average_people_count": round(float(people_counts.mean()), 1) if not people.empty else 0,
            "maximum_people_count": int(people_counts.max()) if not people.empty else 0,
            "minimum_people_count": int(people_counts.min()) if not people.empty else 0,
        },
        "trend": [
            {"timestamp": row.timestamp.isoformat(), "people_count": int(row.people_count)}
            for row in trend.itertuples(index=False)
        ],
        "hourly": [
            {"hour": int(row.hour), "people_count": round(float(row.people_count), 1)}
            for row in hourly_totals.itertuples(index=False)
        ],
        "daily": [
            {"date": row.date, "people_count": round(float(row.people_count), 1)}
            for row in daily_totals.itertuples(index=False)
        ],
        "facility_comparison": [
            {
                "facility_id": row.facility_id,
                "name": row.facility_name,
                "unit": row.unit,
                "average_occupancy_percentage": round(float(row.average_occupancy_percentage), 1),
            }
            for row in facility_means.itertuples(index=False)
        ],
        "capacity_comparison": [
            {
                "facility_id": row.facility_id,
                "name": row.facility_name,
                "unit": row.unit,
                "capacity": int(row.capacity),
                "occupied": int(row.occupied_count),
            }
            for row in latest.itertuples(index=False)
        ],
    }


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, static_folder="frontend", static_url_path="/assets")
    app.config.from_mapping(
        DATA_DIR=PROJECT_DIR / "data",
        DATABASE=PROJECT_DIR / "database" / "campus.sqlite3",
        DATABASE_URL=None,
        APP_ENV=os.environ.get("APP_ENV", "development"),
        OCCUPANCY_THRESHOLDS=dict(THRESHOLDS),
        JSON_SORT_KEYS=False,
    )
    if config:
        app.config.update(config)
    if app.config["DATABASE_URL"] is None:
        app.config["DATABASE_URL"] = os.environ.get("DATABASE_URL")
    if app.config["APP_ENV"] == "production" and not app.config["DATABASE_URL"]:
        raise RuntimeError("DATABASE_URL is required in production.")
    thresholds = app.config["OCCUPANCY_THRESHOLDS"]
    if "OCCUPANCY_THRESHOLDS" not in (config or {}):
        try:
            thresholds = {
                "moderate": float(
                    os.environ.get(
                        "OCCUPANCY_MODERATE_THRESHOLD",
                        thresholds["moderate"],
                    )
                ),
                "high": float(
                    os.environ.get(
                        "OCCUPANCY_HIGH_THRESHOLD",
                        thresholds["high"],
                    )
                ),
            }
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Occupancy thresholds need numeric moderate and high values.") from error
        app.config["OCCUPANCY_THRESHOLDS"] = thresholds
    try:
        moderate = float(app.config["OCCUPANCY_THRESHOLDS"]["moderate"])
        high = float(app.config["OCCUPANCY_THRESHOLDS"]["high"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Occupancy thresholds need numeric moderate and high values.") from error
    if not 0 <= moderate < high <= 100:
        raise ValueError("Occupancy thresholds must satisfy 0 <= moderate < high <= 100.")
    app.config["OCCUPANCY_THRESHOLDS"] = {"moderate": moderate, "high": high}
    database_target = app.config["DATABASE_URL"] or app.config["DATABASE"]
    try:
        engine = initialize_database(database_target, app.config["DATA_DIR"])
        app.extensions["campus_engine"] = engine
        app.extensions["campus_frames"] = load_analysis_frames(engine)
    except Exception:
        app.logger.exception("Campus database initialization failed.")
        raise

    # Render terminates TLS at its proxy; honor its forwarded HTTPS scheme.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    @app.before_request
    def attach_campus_frames() -> None:
        request.environ["campus_frames"] = app.extensions["campus_frames"]

    @app.get("/healthz")
    def health_check():
        try:
            with app.extensions["campus_engine"].connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            app.logger.exception("Health check could not reach the campus database.")
            return jsonify({"status": "unavailable", "database": "unavailable"}), 503
        return jsonify({"status": "ok", "database": "ok"}), 200

    @app.get("/")
    def home():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/overview")
    def overview():
        try:
            observations, campus = _filtered_observations()
        except ValueError as error:
            return _json_error(str(error), 400, "invalid_filter")
        if observations.empty:
            return jsonify(
                {
                    "data_label": DATA_LABEL,
                    "data_kind": "synthetic_historical",
                    "thresholds": app.config["OCCUPANCY_THRESHOLDS"],
                    "as_of": None,
                    "summary": {
                        "facility_count": len(campus),
                        "people_present": 0,
                        "people_capacity": 0,
                        "average_utilization_percentage": 0,
                        "available_library_seats": 0,
                        "available_parking_spaces": 0,
                    },
                    "facilities": [],
                }
            )
        facilities = build_facilities(
            observations, campus, app.config["OCCUPANCY_THRESHOLDS"]
        )
        latest_time = observations["timestamp"].max()
        latest = observations[observations["timestamp"] == latest_time]
        latest_people = latest[latest["unit"] == "people"]
        people_facilities = [item for item in facilities if item["unit"] == "people"]
        by_id = {item["id"]: item for item in facilities}
        return jsonify(
            {
                "data_label": DATA_LABEL,
                "data_kind": "synthetic_historical",
                "thresholds": app.config["OCCUPANCY_THRESHOLDS"],
                "as_of": latest_time.isoformat(),
                "summary": {
                    "facility_count": len(facilities),
                    "people_present": int(latest_people["occupied_count"].sum()),
                    "people_capacity": int(latest_people["capacity"].sum()),
                    "average_utilization_percentage": round(
                        float(pd.Series([f["occupancy_percentage"] for f in people_facilities]).mean()), 1
                    ) if people_facilities else 0,
                    "available_library_seats": by_id.get("library", {}).get("available", 0),
                    "available_parking_spaces": by_id.get("parking", {}).get("available", 0),
                },
                "facilities": facilities,
            }
        )

    @app.get("/api/facilities")
    def facilities():
        try:
            observations, campus = _filtered_observations()
        except ValueError as error:
            return _json_error(str(error), 400, "invalid_filter")
        return jsonify(
            {
                "data_label": DATA_LABEL,
                "thresholds": app.config["OCCUPANCY_THRESHOLDS"],
                "facilities": build_facilities(
                    observations, campus, app.config["OCCUPANCY_THRESHOLDS"]
                ),
            }
        )

    @app.get("/api/facility/<location_id>")
    def facility_detail(location_id: str):
        try:
            observations, campus = _filtered_observations()
        except ValueError as error:
            return _json_error(str(error), 400, "invalid_filter")
        known_ids = set(campus["building_id"].astype(str))
        if location_id not in known_ids:
            return _json_error("No campus facility has that ID.", 404, "facility_not_found")
        rows = observations[observations["facility_id"] == location_id].sort_values("timestamp")
        if rows.empty:
            return _json_error("No samples are available for this facility and filter.", 404, "no_samples")
        current = rows.iloc[-1]
        building = campus[campus["building_id"] == location_id].iloc[0]
        return jsonify(
            {
                "data_label": DATA_LABEL,
                "facility": {
                    "id": location_id,
                    "name": str(building["building_name"]),
                    "type": str(building["building_type"]),
                    "capacity": int(current["capacity"]),
                    "occupied": int(current["occupied_count"]),
                    "available": int(current["available_count"]),
                    "occupancy_percentage": float(current["occupancy_percentage"]),
                    "status": status_for(
                        float(current["occupancy_percentage"]),
                        app.config["OCCUPANCY_THRESHOLDS"],
                    ),
                    "unit": str(current["unit"]),
                    "as_of": current["timestamp"].isoformat(),
                    "average_occupancy_percentage": round(float(rows["occupancy_percentage"].mean()), 1),
                    "maximum_occupancy_percentage": round(float(rows["occupancy_percentage"].max()), 1),
                    "minimum_occupancy_percentage": round(float(rows["occupancy_percentage"].min()), 1),
                    "history": [
                        {
                            "timestamp": row.timestamp.isoformat(),
                            "occupied": int(row.occupied_count),
                            "capacity": int(row.capacity),
                            "occupancy_percentage": round(float(row.occupancy_percentage), 1),
                        }
                        for row in rows.itertuples(index=False)
                    ],
                },
            }
        )

    @app.get("/api/crowd")
    def crowd():
        try:
            observations, _ = _filtered_observations()
        except ValueError as error:
            return _json_error(str(error), 400, "invalid_filter")
        people = observations[observations["unit"] == "people"]
        return jsonify({"data_label": DATA_LABEL, "records": [
            {
                "timestamp": row.timestamp.isoformat(),
                "location_id": row.facility_id,
                "location_name": row.facility_name,
                "people_count": int(row.occupied_count),
                "capacity": int(row.capacity),
                "occupancy_percentage": round(float(row.occupancy_percentage), 1),
            }
            for row in people.itertuples(index=False)
        ]})

    @app.get("/api/analytics")
    def analytics():
        try:
            observations, _ = _filtered_observations()
        except ValueError as error:
            return _json_error(str(error), 400, "invalid_filter")
        payload = _analytics_payload(observations)
        payload["data_label"] = DATA_LABEL
        return jsonify(payload)

    @app.get("/api/insights")
    def insights():
        try:
            observations, _ = _filtered_observations()
        except ValueError as error:
            return _json_error(str(error), 400, "invalid_filter")
        return jsonify(
            {
                "data_label": DATA_LABEL,
                "thresholds": app.config["OCCUPANCY_THRESHOLDS"],
                "insights": build_insights(
                    observations, app.config["OCCUPANCY_THRESHOLDS"]
                ),
            }
        )

    @app.get("/api/notifications")
    def notifications():
        try:
            observations, _ = _filtered_observations()
        except ValueError as error:
            return _json_error(str(error), 400, "invalid_filter")
        alerts = [
            item for item in build_insights(
                observations, app.config["OCCUPANCY_THRESHOLDS"]
            )
            if item["severity"] in {"high", "info"}
        ]
        return jsonify(
            {
                "data_label": DATA_LABEL,
                "notifications": alerts,
                "unread_count": sum(item["severity"] == "high" for item in alerts),
            }
        )

    @app.errorhandler(DatasetError)
    def dataset_error(error: DatasetError):
        app.logger.error("Dataset initialization failed: %s", error)
        return _json_error("Campus datasets could not be loaded.", 500, "dataset_error")

    @app.errorhandler(404)
    def not_found(_error):
        return _json_error("The requested page or API route does not exist.", 404, "not_found")

    return app


app = create_app()


if __name__ == "__main__":
    # Render supplies PORT; local runs default to port 5000.
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
        use_reloader=False,
    )
