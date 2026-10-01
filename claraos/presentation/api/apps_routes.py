"""Thin HTTP adapter for App Hub use cases."""

from fastapi import APIRouter, HTTPException

from ...application.apps.service import AppHubService


def build_apps_router(service: AppHubService) -> APIRouter:
    router = APIRouter()

    @router.get("/catalog")
    async def get_catalog():
        return await service.list_installed_apps()

    @router.get("/store")
    async def get_store():
        return await service.list_store_apps()

    @router.post("/{app_id}/install")
    async def install_app(app_id: str):
        # Installation is intentionally held until the authenticated OMV Compose
        # gateway is introduced. This route preserves the public API shape.
        raise HTTPException(
            status_code=409,
            detail="Compose Store chưa được kích hoạt: cần OMV Compose gateway có xác thực.",
        )

    return router
