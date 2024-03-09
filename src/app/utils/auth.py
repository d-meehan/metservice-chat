from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request path: {request.url.path}")
        if request.url.path == '/':
            return RedirectResponse(url='/login')
        response = await call_next(request)
        return response
