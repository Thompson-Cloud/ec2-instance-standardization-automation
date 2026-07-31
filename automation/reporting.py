import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPORT_FIELDS = [
    "run_id",
    "instance_name",
    "instance_id",
    "role",
    "availability_zone",
    "original_type",
    "target_type",
    "original_state",
    "final_state",
    "result",
    "rollback_result",
    "error",
    "started_at",
    "completed_at",
]


def generate_run_id() -> str:
    """Create a unique identifier for an automation run."""

    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_reports(
    results: list[dict[str, Any]],
    run_metadata: dict[str, Any],
) -> tuple[Path, Path, Path]:
    """
    Generate CSV, JSON, and Markdown reports.

    Args:
        results: Per-instance execution results.
        run_metadata: Information about the overall automation run.

    Returns:
        Paths to the CSV, JSON, and Markdown reports.
    """

    reports_directory = Path(__file__).parent / "reports"
    reports_directory.mkdir(parents=True, exist_ok=True)

    run_id = run_metadata["run_id"]

    csv_path = reports_directory / f"resize-report-{run_id}.csv"
    json_path = reports_directory / f"resize-report-{run_id}.json"
    markdown_path = reports_directory / f"resize-report-{run_id}.md"

    write_csv_report(
        csv_path,
        results,
    )

    write_json_report(
        json_path,
        results,
        run_metadata,
    )

    write_markdown_report(
        markdown_path,
        results,
        run_metadata,
    )

    return csv_path, json_path, markdown_path


def write_csv_report(
    csv_path: Path,
    results: list[dict[str, Any]],
) -> None:
    """
    Write a spreadsheet-friendly CSV report.

    Args:
        csv_path: Destination path for the CSV file.
        results: Per-instance execution results.
    """

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=REPORT_FIELDS,
            extrasaction="ignore",
        )

        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    field: result.get(field, "")
                    for field in REPORT_FIELDS
                }
            )


def write_json_report(
    json_path: Path,
    results: list[dict[str, Any]],
    run_metadata: dict[str, Any],
) -> None:
    """
    Write a machine-readable JSON report.

    Args:
        json_path: Destination path for the JSON file.
        results: Per-instance execution results.
        run_metadata: Information about the overall automation run.
    """

    summary = build_summary(results)

    report = {
        "run": {
            **run_metadata,
            "summary": summary,
        },
        "instances": results,
    }

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            default=str,
        )


def write_markdown_report(
    markdown_path: Path,
    results: list[dict[str, Any]],
    run_metadata: dict[str, Any],
) -> None:
    """
    Write an engineer-friendly Markdown report.

    Args:
        markdown_path: Destination path for the Markdown file.
        results: Per-instance execution results.
        run_metadata: Information about the overall automation run.
    """

    summary = build_summary(results)

    lines = [
        "# EC2 Instance Resize Report",
        "",
        "## Run Summary",
        "",
        f"- **Run ID:** {run_metadata.get('run_id', 'N/A')}",
        f"- **AWS Account:** {run_metadata.get('account_id', 'N/A')}",
        f"- **Region:** {run_metadata.get('region', 'N/A')}",
        f"- **Application:** {run_metadata.get('application', 'N/A')}",
        f"- **Environment:** {run_metadata.get('environment', 'N/A')}",
        f"- **Execution Mode:** "
        f"{run_metadata.get('execution_mode', 'N/A')}",
        f"- **Source Instance Type:** "
        f"{run_metadata.get('source_instance_type', 'N/A')}",
        f"- **Target Instance Type:** "
        f"{run_metadata.get('target_instance_type', 'N/A')}",
        f"- **Started At:** "
        f"{run_metadata.get('started_at', 'N/A')}",
        f"- **Completed At:** "
        f"{run_metadata.get('completed_at', 'N/A')}",
        f"- **Overall Status:** "
        f"{run_metadata.get('overall_status', 'N/A')}",
        "",
    ]

    validation_errors = run_metadata.get(
        "validation_errors",
        [],
    )

    if validation_errors:
        lines.extend(
            [
                "## Validation Errors",
                "",
            ]
        )

        for error in validation_errors:
            lines.append(
                f"- {escape_markdown(error)}"
            )

        lines.append("")

    lines.extend(
        [
            "## Results Summary",
            "",
            "| Metric | Count |",
            "|---|---:|",
            f"| Total Results | {summary['total_results']} |",
            f"| Successful | {summary['successful']} |",
            f"| Failed | {summary['failed']} |",
            f"| Rolled Back | {summary['rolled_back']} |",
            f"| Rollback Failed | {summary['rollback_failed']} |",
            "",
            "## Instance Results",
            "",
            "| Instance | Role | Availability Zone | Original Type | "
            "Target Type | Final State | Result | Rollback | Error |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )

    if not results:
        lines.append(
            "| No instances processed | - | - | - | - | - | - | - | - |"
        )
    else:
        for result in results:
            lines.append(
                "| "
                f"{escape_markdown(result.get('instance_name', 'N/A'))} | "
                f"{escape_markdown(result.get('role', 'N/A'))} | "
                f"{escape_markdown(result.get('availability_zone', 'N/A'))} | "
                f"{escape_markdown(result.get('original_type', 'N/A'))} | "
                f"{escape_markdown(result.get('target_type', 'N/A'))} | "
                f"{escape_markdown(result.get('final_state', 'N/A'))} | "
                f"{escape_markdown(result.get('result', 'N/A'))} | "
                f"{escape_markdown(result.get('rollback_result', 'N/A'))} | "
                f"{escape_markdown(result.get('error', ''))} |"
            )

    failed_results = [
        result
        for result in results
        if result.get("result") == "failed"
    ]

    if failed_results:
        lines.extend(
            [
                "",
                "## Failure Details",
                "",
            ]
        )

        for result in failed_results:
            lines.extend(
                [
                    f"### "
                    f"{escape_markdown(result.get('instance_name', 'Unknown instance'))}",
                    "",
                    f"- **Instance ID:** "
                    f"{escape_markdown(result.get('instance_id', 'N/A'))}",
                    f"- **Result:** "
                    f"{escape_markdown(result.get('result', 'N/A'))}",
                    f"- **Rollback Result:** "
                    f"{escape_markdown(result.get('rollback_result', 'N/A'))}",
                    f"- **Error:** "
                    f"{escape_markdown(result.get('error', 'No error provided'))}",
                    "",
                ]
            )

    markdown_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def build_summary(
    results: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Calculate execution totals from instance results.

    Args:
        results: Per-instance execution results.

    Returns:
        Summary counts.
    """

    return {
        "total_results": len(results),
        "successful": sum(
            1
            for result in results
            if result.get("result") == "success"
        ),
        "failed": sum(
            1
            for result in results
            if result.get("result") == "failed"
        ),
        "rolled_back": sum(
            1
            for result in results
            if result.get("rollback_result") == "success"
        ),
        "rollback_failed": sum(
            1
            for result in results
            if result.get("rollback_result") == "failed"
        ),
    }


def escape_markdown(value: Any) -> str:
    """
    Escape values so they render safely inside Markdown tables.

    Args:
        value: Value to format.

    Returns:
        Markdown-safe text.
    """

    if value is None:
        return ""

    return (
        str(value)
        .replace("|", "\\|")
        .replace("\n", " ")
    )