from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger


class ReelsBotException(Exception):
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ContentGenerationError(ReelsBotException):
    
    def __init__(self, message: str = "Failed to generate content"):
        super().__init__(message, status_code=422)


class APIKeyError(ReelsBotException):
    
    def __init__(self, service: str):
        message = f"Invalid or missing API key for {service}"
        super().__init__(message, status_code=401)


class RateLimitError(ReelsBotException):
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class ValidationError(ReelsBotException):
    
    def __init__(self, message: str = "Invalid input data"):
        super().__init__(message, status_code=400)


async def reelsbot_exception_handler(
    request: Request, exc: ReelsBotException
) -> JSONResponse:
    logger.error(f"ReelsBot exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": exc.__class__.__name__,
            "path": str(request.url)
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "type": "InternalServerError",
            "path": str(request.url)
        }
    )


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ReelsBotException, reelsbot_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)