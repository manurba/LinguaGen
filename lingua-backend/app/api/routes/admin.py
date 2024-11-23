from fastapi import APIRouter, Depends, HTTPException
from app.services.admin import AdminService
from app.core.dependencies import verify_token

router = APIRouter()
admin_service = AdminService()

@router.get("/users")
async def get_users(admin_data: dict = Depends(verify_token)):
    if not admin_data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return await admin_service.get_all_users()

@router.post("/whitelist")
async def add_to_whitelist(
    email: str,
    admin_data: dict = Depends(verify_token)
):
    if not admin_data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return await admin_service.add_to_whitelist(email)
