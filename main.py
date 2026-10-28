
from pathlib import Path
import os
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_FILE = DATA_DIR / "shipments.csv"

REQUIRED_COLUMNS = [
    "container_id",
    "origin",
    "destination",
    "departure_date",
    "estimated_arrival",
    "actual_arrival",
    "transit_days",
]


def load_data(path: Path) -> pd.DataFrame:
    """Load shipment records and validate required columns."""

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_csv(path)

    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: {missing_columns}"
        )

    # Clean text columns.
    for col in ["container_id", "origin", "destination"]:
        df[col] = df[col].astype("string").str.strip()

    # Convert date columns.
    for col in [
        "departure_date",
        "estimated_arrival",
        "actual_arrival",
    ]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Convert transit duration to a number.
    df["transit_days"] = pd.to_numeric(
        df["transit_days"], errors="coerce"
    )

    return df


def validate_data(df: pd.DataFrame):
    """Return clean records, data-quality issues, and a summary."""

    work = df.copy()
    work.insert(0, "source_row", range(2, len(work) + 2))

    issues = []

    def add_issue(mask, issue_type, details):
        mask = mask.fillna(False)

        for idx in work.index[mask]:
            issues.append({
                "source_row": int(work.at[idx, "source_row"]),
                "container_id": work.at[idx, "container_id"],
                "issue_type": issue_type,
                "details": details,
            })

    # 1. Check required fields.
    required_fields = [
        "container_id",
        "origin",
        "destination",
        "departure_date",
        "estimated_arrival",
    ]

    for col in required_fields:
        missing_mask = work[col].isna()

        if work[col].dtype == "string":
            missing_mask = missing_mask | work[col].eq("")

        add_issue(
            missing_mask,
            "MISSING_REQUIRED_VALUE",
            f"Required field '{col}' is missing or blank",
        )

    # 2. Check duplicate container IDs after the first occurrence.
    duplicate_mask = (
        work["container_id"].notna()
        & work["container_id"].ne("")
        & work["container_id"].duplicated(keep="first")
    )

    add_issue(
        duplicate_mask,
        "DUPLICATE_CONTAINER_ID",
        "Container ID appears more than once",
    )

    # 3. Check estimated arrival before departure.
    estimated_arrival_mask = (
        work["departure_date"].notna()
        & work["estimated_arrival"].notna()
        & (
            work["estimated_arrival"]
            < work["departure_date"]
        )
    )

    add_issue(
        estimated_arrival_mask,
        "ARRIVAL_BEFORE_DEPARTURE",
        "Estimated arrival is earlier than departure",
    )

    # 4. Check negative transit duration.
    negative_transit_mask = (
        work["transit_days"].notna()
        & (work["transit_days"] < 0)
    )

    add_issue(
        negative_transit_mask,
        "NEGATIVE_TRANSIT_DAYS",
        "Transit duration cannot be negative",
    )

    # 5. Check actual arrival before departure.
    actual_arrival_mask = (
        work["actual_arrival"].notna()
        & work["departure_date"].notna()
        & (
            work["actual_arrival"]
            < work["departure_date"]
        )
    )

    add_issue(
        actual_arrival_mask,
        "ACTUAL_ARRIVAL_BEFORE_DEPARTURE",
        "Actual arrival is earlier than departure",
    )

    # 6. Compare recorded transit days with estimated duration.
    calculated_days = (
        work["estimated_arrival"] - work["departure_date"]
    ).dt.total_seconds() / 86400

    discrepancy_mask = (
        work["transit_days"].notna()
        & calculated_days.notna()
        & (
            (work["transit_days"] - calculated_days).abs()
            > 2
        )
    )

    add_issue(
        discrepancy_mask,
        "TRANSIT_DURATION_MISMATCH",
        (
            "Recorded transit_days differs from the "
            "departure-to-estimated-arrival duration "
            "by more than 2 days"
        ),
    )

    # Create the issue report.
    issues_df = pd.DataFrame(
        issues,
        columns=[
            "source_row",
            "container_id",
            "issue_type",
            "details",
        ],
    )

    # Exclude every row that has at least one issue.
    if not issues_df.empty:
        issue_rows = set(issues_df["source_row"])
    else:
        issue_rows = set()

    clean = (
        work.loc[~work["source_row"].isin(issue_rows)]
        .drop(columns=["source_row"])
        .copy()
    )

    # Create the quality summary.
    summary = pd.DataFrame([
        {
            "metric": "total_input_rows",
            "value": len(work),
        },
        {
            "metric": "clean_rows",
            "value": len(clean),
        },
        {
            "metric": "rows_flagged_for_review",
            "value": len(issue_rows),
        },
        {
            "metric": "total_issues_found",
            "value": len(issues_df),
        },
        {
            "metric": "duplicate_container_id_issues",
            "value": (
                int(
                    (
                        issues_df["issue_type"]
                        == "DUPLICATE_CONTAINER_ID"
                    ).sum()
                )
                if not issues_df.empty
                else 0
            ),
        },
        {
            "metric": "missing_required_value_issues",
            "value": (
                int(
                    (
                        issues_df["issue_type"]
                        == "MISSING_REQUIRED_VALUE"
                    ).sum()
                )
                if not issues_df.empty
                else 0
            ),
        },
    ])

    return clean, issues_df, summary


def write_outputs(
    clean: pd.DataFrame,
    issues: pd.DataFrame,
    summary: pd.DataFrame,
):
    """Save the cleaned data, issues, and summary as CSV files."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Convert dates to consistent strings before saving.
    clean_output = clean.copy()
    issues_output = issues.copy()
    summary_output = summary.copy()

    for output_df in [clean_output, issues_output, summary_output]:
        for col in output_df.select_dtypes(
            include=["datetime64[ns]", "datetimetz"]
        ).columns:
            output_df[col] = output_df[col].dt.strftime(
                "%Y-%m-%d"
            )

    clean_output.to_csv(
        OUTPUT_DIR / "clean_shipments.csv",
        index=False,
    )

    issues_output.to_csv(
        OUTPUT_DIR / "data_quality_issues.csv",
        index=False,
    )

    summary_output.to_csv(
        OUTPUT_DIR / "quality_summary.csv",
        index=False,
    )


def load_to_mysql(
    clean: pd.DataFrame,
    issues: pd.DataFrame,
):
    """Optionally load results into MySQL when MYSQL_URL is configured."""

    try:
        from dotenv import load_dotenv

        load_dotenv(BASE_DIR / ".env")
    except ImportError:
        pass

    mysql_url = os.getenv("MYSQL_URL")

    # MySQL is optional. CSV reports are generated without it.
    if not mysql_url:
        print(
            "\nMYSQL_URL not set; skipping MySQL load. "
            "CSV reports were created."
        )
        return

    # Import SQLAlchemy only when MySQL is requested.
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.exc import SQLAlchemyError

        engine = create_engine(
            mysql_url,
            pool_pre_ping=True,
        )

        with engine.begin() as connection:
            clean.to_sql(
                "clean_shipments",
                con=connection,
                if_exists="replace",
                index=False,
            )

            issues.to_sql(
                "data_quality_issues",
                con=connection,
                if_exists="replace",
                index=False,
            )

        print(
            "Loaded clean_shipments and "
            "data_quality_issues tables into MySQL."
        )

    except ImportError as exc:
        print(f"MySQL dependencies are unavailable: {exc}")
        print("The CSV reports were still created.")

    except Exception as exc:
        print(f"MySQL load failed: {exc}")
        print(
            "Check your .env credentials, database name, "
            "MySQL server, and Windows security restrictions."
        )


def main():
    """Run the complete data-quality pipeline."""

    print("Starting shipment data-quality pipeline...")

    df = load_data(INPUT_FILE)

    clean, issues, summary = validate_data(df)

    write_outputs(clean, issues, summary)

    print("\nDATA QUALITY SUMMARY")
    print(summary.to_string(index=False))

    print("\nOUTPUT FILES")
    print(f"Clean records: {OUTPUT_DIR / 'clean_shipments.csv'}")
    print(f"Issue report:  {OUTPUT_DIR / 'data_quality_issues.csv'}")
    print(f"Summary:       {OUTPUT_DIR / 'quality_summary.csv'}")

    load_to_mysql(clean, issues)

    print("\nPipeline finished.")


if __name__ == "__main__":
    main()
