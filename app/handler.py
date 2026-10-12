import json
import os
import platform
from urllib.parse import parse_qs


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json; charset=utf-8", "cache-control": "no-store"},
        "body": json.dumps(body),
    }


def handler(event, context):
    """Handle a Lambda Function URL HTTP event."""
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    if method != "GET":
        return response(405, {"error": "method_not_allowed", "allowed": ["GET"]})

    query = parse_qs(event.get("rawQueryString", ""))
    name = query.get("name", ["world"])[0].strip()
    if len(name) > 80:
        return response(400, {"error": "name_too_long", "max_length": 80})
    if not name:
        name = "world"

    return response(200, {
        "status": "ok",
        "message": "Python service is healthy",
        "greeting": f"Hello, {name}!",
        "runtime": {
            "python": platform.python_version(),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "request_id": getattr(context, "aws_request_id", "local-test"),
        },
    })
