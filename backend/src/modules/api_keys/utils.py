"""Utility functions for API key analytics and data processing."""

from datetime import datetime
from typing import Any


def calculate_basic_metrics(usage_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate basic usage metrics from usage records.

    Args:
        usage_records: List of usage record dictionaries

    Returns:
        Dictionary containing basic metrics
    """
    total_requests = len(usage_records)
    successful_requests = len([u for u in usage_records if isinstance(u, dict) and 200 <= u.get("status_code", 0) < 300])
    failed_requests = total_requests - successful_requests

    total_tokens = sum(u.get("tokens_used", 0) or 0 for u in usage_records if isinstance(u, dict))

    total_cost = sum(u.get("cost_microcents", 0) or 0 for u in usage_records if isinstance(u, dict))

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
    }


def calculate_response_time_metrics(usage_records: list[dict[str, Any]]) -> float | None:
    """Calculate average response time from usage records.

    Args:
        usage_records: List of usage record dictionaries

    Returns:
        Average response time in milliseconds or None if no data
    """
    response_times = []
    for u in usage_records:
        if isinstance(u, dict) and u.get("response_time_ms") is not None:
            response_times.append(u["response_time_ms"])

    return sum(response_times) / len(response_times) if response_times else None


def calculate_endpoint_usage(usage_records: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    """Calculate most used endpoints from usage records.

    Args:
        usage_records: List of usage record dictionaries
        limit: Maximum number of endpoints to return

    Returns:
        List of endpoint usage dictionaries sorted by count
    """
    endpoint_counts: dict[str, int] = {}
    for record in usage_records:
        if isinstance(record, dict):
            endpoint = record.get("endpoint", "")
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

    return [
        {"endpoint": endpoint, "count": count}
        for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    ]


def calculate_error_breakdown(usage_records: list[dict[str, Any]]) -> dict[str, int]:
    """Calculate error status code breakdown from usage records.

    Args:
        usage_records: List of usage record dictionaries

    Returns:
        Dictionary mapping status codes to counts
    """
    error_counts: dict[str, int] = {}
    for record in usage_records:
        if isinstance(record, dict) and record.get("status_code", 0) >= 400:
            status = record.get("status_code", 0)
            error_counts[str(status)] = error_counts.get(str(status), 0) + 1

    return error_counts


def calculate_daily_usage(usage_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calculate daily usage breakdown from usage records.

    Args:
        usage_records: List of usage record dictionaries

    Returns:
        List of daily usage dictionaries sorted by date
    """
    daily_usage: dict[str, dict[str, Any]] = {}

    for record in usage_records:
        if not isinstance(record, dict) or not record.get("created_at"):
            continue

        created_at = record["created_at"]
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

        day_key = created_at.strftime("%Y-%m-%d")
        if day_key not in daily_usage:
            daily_usage[day_key] = {
                "date": day_key,
                "requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "tokens": 0,
                "cost_microcents": 0,
            }

        daily_usage[day_key]["requests"] += 1
        if 200 <= record.get("status_code", 0) < 300:
            daily_usage[day_key]["successful_requests"] += 1
        else:
            daily_usage[day_key]["failed_requests"] += 1
        daily_usage[day_key]["tokens"] += record.get("tokens_used", 0) or 0
        daily_usage[day_key]["cost_microcents"] += record.get("cost_microcents", 0) or 0

    return sorted(daily_usage.values(), key=lambda x: x["date"])


def parse_usage_records(result: Any) -> list[dict[str, Any]]:
    """Parse usage records from database result.

    Args:
        result: Database query result

    Returns:
        List of usage record dictionaries
    """
    usage_records: list[dict[str, Any]] = []
    if isinstance(result, dict) and result.get("data"):
        data = result["data"]
        if isinstance(data, list):
            usage_records = data

    return usage_records
