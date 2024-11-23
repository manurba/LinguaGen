from fastapi import APIRouter, HTTPException
from app.services.auth import AuthService
from app.api.models.auth import GoogleLoginRequest

router = APIRouter()
auth_service = AuthService()

@router.post("/google-login")
async def google_login(request: GoogleLoginRequest):
    """
    Endpoint for Google OAuth login
    Expects a JSON body: {"code": "your_google_auth_code"}
    """
    try:
        return await auth_service.google_auth(request.code)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_token(token: str):
    return await auth_service.verify_token(token)

# Add a test endpoint to verify router is working
@router.get("/test")
async def test_auth():
    return {"message": "Auth router is working"}
