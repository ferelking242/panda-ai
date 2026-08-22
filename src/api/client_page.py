"""
Client page — redirects to the Next.js dashboard.

The actual client UI lives in the dashboard/ Next.js app.
This endpoint exists only so legacy /client links still work.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

dashboard_client_router = APIRouter(tags=["client"])


@dashboard_client_router.get("/client", response_class=RedirectResponse)
async def serve_client():
    """Redirect /client to the dashboard's client page."""
    return RedirectResponse(url="/dashboard/client", status_code=302)
