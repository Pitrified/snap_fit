"""Router: settings API endpoints."""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends

from snap_fit.webapp.core.settings import Settings
from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.schemas.settings import SetDatasetRequest

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/datasets", summary="List available datasets")
async def list_datasets(
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[str]:
    """Return tag names that have a dataset.db in the cache directory."""
    return settings.available_datasets()


@router.get("/current", summary="Get current dataset")
async def get_current(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str | None]:
    """Return the currently active dataset tag."""
    return {"dataset": settings.active_dataset}


@router.post("/dataset", summary="Set current dataset")
async def set_dataset(
    body: SetDatasetRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str | None]:
    """Set the active dataset tag (None clears the selection)."""
    settings.set_dataset(body.tag)
    return {"dataset": settings.active_dataset}
