from fastapi import APIRouter
from starlette.responses import Response
import prometheus_client

from app.core.metrics import REGISTRY

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)

@router.get("/metrics")
async def metrics():
    """
    Endpoint for exposing Prometheus metrics
    """
    return Response(
        prometheus_client.generate_latest(REGISTRY),
        media_type="text/plain"
    )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for kubernetes/service mesh
    """
    return {"status": "healthy"}
