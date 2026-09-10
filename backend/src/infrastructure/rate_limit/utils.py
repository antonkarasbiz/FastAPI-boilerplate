def sanitize_path(path: str) -> str:
    """Sanitize API path for use in rate limiting keys."""
    return path.strip("/").replace("/", "_")
