"""HTTP status code enumeration."""

from enum import Enum


class StatusCode(int, Enum):
    """HTTP status codes used in API responses."""

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    NOT_FOUND = 404
    UNPROCESSABLE = 422
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503
