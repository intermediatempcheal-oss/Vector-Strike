"""Friendly, consistent API error responses.

Raw Django/server error strings are never passed straight to users; the
frontend receives a stable shape::

    {"error": {"code": "...", "message": "...", "fields": {...}}}

"""

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class VectorError(APIException):
    """Base class for domain errors raised by Vector Strike APIs."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Something went wrong. Please try again."
    default_code = "vector_error"

    def __init__(self, detail=None, code=None, fields=None):
        self.fields = fields
        super().__init__(detail, code)


class ValidationFailed(VectorError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = "validation_failed"


class ConflictError(VectorError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"


class RateLimited(VectorError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_code = "rate_limited"


def reshape(detail):
    """Convert DRF validation detail into shape {field: [messages] or message}."""
    if isinstance(detail, (list, tuple)):
        return {"_error": [str(d) for d in detail]}
    if isinstance(detail, dict):
        return {k: reshape(v) for k, v in detail.items()}
    return {"_error": [str(detail)]}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        # Handle unexpected runtime errors gracefully in production.
        from django.conf import settings

        code = "server_error"
        message = "We couldn't complete that right now. Please try again."
        if settings.DEBUG:
            message = f"{type(exc).__name__}: {exc}"
        response = exc_response(status.HTTP_500_INTERNAL_SERVER_ERROR, code, message, {})
        return response

    # Field-level validation failures are most naturally expressed as a 422
    # so the frontend can distinguish "your input" from "the request" errors.
    from rest_framework.exceptions import ValidationError as DrfValidationError

    detail = getattr(exc, "detail", None)
    fields = reshape(detail) if detail is not None else {}
    message = (
        next(iter(fields.values()), "Something went wrong.") if fields else None
    )
    if isinstance(message, (list, tuple)):
        message = message[0] if message else "Something went wrong."
    if isinstance(message, dict):
        message = "Please review the highlighted fields."
    if message is None:
        message = getattr(exc, "detail", None) or "Something went wrong."
        if isinstance(message, (list, tuple)):
            message = message[0] if message else "Something went wrong."
        if isinstance(message, dict):
            message = "Please review the highlighted fields."
    code = getattr(exc, "default_code", "error")

    if isinstance(exc, DrfValidationError):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        message = "You're moving too fast. Give it a moment and try again."

    response.data = {
        "error": {
            "code": code,
            "message": str(message),
            "fields": fields if fields else {},
        }
    }
    return response


def exc_response(http_status, code, message, fields):
    from rest_framework.response import Response

    return Response(
        {"error": {"code": code, "message": message, "fields": fields}},
        status=http_status,
    )