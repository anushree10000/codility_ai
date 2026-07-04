from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    content = {"detail": exc.detail}
    if exc.error_code:
        content["error_code"] = exc.error_code
    return JSONResponse(status_code=exc.status_code, content=content)


async def generic_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
