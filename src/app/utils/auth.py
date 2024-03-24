
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, Client
from starlette.middleware.base import BaseHTTPMiddleware

unrestricted_page_routes = {'/login'}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if request.url.path in Client.page_routes.values() and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path
                return RedirectResponse('/login')
        return await call_next(request)
