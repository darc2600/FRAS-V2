from fastapi import APIRouter
from fastapi import Request

router = APIRouter()

@router.get("/api/routes")
async def list_routes(request: Request):
    return [route.path for route in request.app.routes]
