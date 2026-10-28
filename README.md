# Shipment Data Quality Validation and Anomaly Detection

A portfolio project demonstrating practical data-quality checks with Python, Pandas, CSV, and optional MySQL. The sample shipment data is fictional and created only for practice.

## Features
- Checks required fields for missing or blank values.
- Flags repeated container IDs.
- Validates estimated and actual arrival dates against departure dates.
- Flags negative transit durations.
- Flags differences between recorded transit duration and the date-based estimate.
- Produces clean data, an issue-level report, and a summary CSV.
- Optionally loads output tables into MySQL.

## Project structure
```text
portcast_data_quality_project/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   └── shipments.csv
├── sql/
│   ├── schema.sql
│   └── analysis_queries.sql
└── output/                 # generated when the script runs
```

## Requirements
- Python 3.10 or newer
- Internet access for installing packages
- Optional: MySQL Server and MySQL Workbench

## Run it on Windows
Open Command Prompt in this folder and run:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

The script creates:
- `output/clean_shipments.csv`
- `output/data_quality_issues.csv`
- `output/quality_summary.csv`

Rows with any detected issue are sent to the issue report and excluded from the clean dataset. This is a conservative demo rule; in a production pipeline, severity rules and business-specific decisions should determine whether a record is rejected, quarantined, or corrected.

## Optional MySQL setup
1. Start MySQL Server.
2. Run `sql/schema.sql` in MySQL Workbench to create the database.
3. Copy `.env.example` to `.env`.
4. Replace the username and password in `MYSQL_URL`.
5. Run `python main.py` again.

Example URL:
`mysql+pymysql://root:your_password@localhost:3306/portcast_data_quality`

The script replaces the two output tables each run. Use a dedicated practice database only. Do not use production credentials or real customer data.

## Important interpretation
- `estimated_arrival` must parse as a date and should not be earlier than departure.
- `actual_arrival` is optional because shipments may not yet have arrived.
- A transit-duration mismatch is flagged for review, not automatically treated as proof that the record is wrong.
- Duplicate detection currently flags repeated container IDs after the first occurrence. If one container can legitimately have multiple event rows, define a composite business key instead.

## Resume wording (only after you have run and understood the project)
**Shipment Data Quality Validation and Anomaly Detection | Python, Pandas, MySQL**
- Built a data-quality workflow to flag missing fields, duplicate container IDs, invalid date sequences, and inconsistent transit durations.
- Generated clean shipment data, issue-level reports, and a quality summary for review.
- Used SQL queries to inspect issue patterns and validate processed records.

Be prepared to explain your validation rules, why questionable rows are flagged, and how you would adapt checks for real shipment data.
