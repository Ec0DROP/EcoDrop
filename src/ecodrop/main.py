"""FastAPI application: router registration and exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ecodrop import __version__
from ecodrop.api import claims, donations
from ecodrop.core.exceptions import EcoDropError


async def handle_ecodrop_error(_request: Request, exc: EcoDropError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.code, "detail": exc.detail}
    )


def create_app() -> FastAPI:
    app = FastAPI(title="EcoDrop API", version=__version__)
    app.include_router(donations.router)
    app.include_router(claims.router)
    app.add_exception_handler(EcoDropError, handle_ecodrop_error)
    return app


app = create_app()
