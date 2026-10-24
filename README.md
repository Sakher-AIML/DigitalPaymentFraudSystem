# Digital Payment Transaction Monitoring & Fraud Risk Management System

Academic B.Tech AI/ML project for DCDS at Symbiosis Institute of Technology. The application is a Streamlit fintech console using fictional payment data. Fraud detection is deliberately explainable and rule-based; it does not claim to use a trained model.

## Architecture

- **MySQL 8** is authoritative for customers, accounts, merchants, transactions, alerts, and cases. Stored procedures protect settlement and case workflows.
- **MongoDB** stores transaction telemetry and investigation audit events.
- **Python/Streamlit** provides six pages: Dashboard, Transaction Monitoring, Submit / Simulate, Fraud Alerts, Investigation Cases, and System Status.

## Setup

1. Install Python 3.13 and MySQL 8/MongoDB locally.
2. Create an environment and install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set local credentials. Never commit `.env`.
4. Import `sql/schema.sql`, then `sql/seed.sql`, using a MySQL client.
5. Run `python scripts/setup_check.py`.
6. Start the UI with `streamlit run app/main.py`.
7. Run unit tests with `pytest -q`.

If Python or either database is unavailable, the project files remain usable but live integration cannot be verified. The System Status page reports actionable connection errors and never claims a write succeeded when it did not.

## Fraud rules

`R-VEL-01` detects velocity, `R-AMT-01` high value, `R-BAL-01` insufficient funds, `R-DEV-01` unusual devices, `R-REP-01` repeated failed attempts, and `R-MCC-01` configured high-risk merchant categories. Points are deduplicated and capped at 100. Scores map to LOW, MEDIUM, HIGH, or CRITICAL thresholds in `.env`; alerts are review signals, not proof of fraud.

## Common errors

- **MySQL access denied:** confirm `MYSQL_HOST`, `MYSQL_PORT`, user, and password in `.env`.
- **Table does not exist:** import `schema.sql` before `seed.sql`.
- **MongoDB timeout:** start the local MongoDB service and verify `MONGO_URI`.
- **No dashboard data:** run the seed script and refresh the app.

## Limitations and future scope

This academic demo uses fictional data, rule-based scoring, and local services. Future work could add role-based access, richer time-series analysis, alert notifications, and a formally reviewed model only after governance and representative data are available.
