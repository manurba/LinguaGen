from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException
from datetime import datetime, timedelta
import jwt
import logging
from app.core.config import settings

class AuthService:
    async def google_auth(self, code: str):
        try:
            # Create the flow using the client secrets
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uri": settings.REDIRECT_URI,
                    }
                },
                scopes=[
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "openid",
                ]
            )

            # Set the redirect URI
            flow.redirect_uri = settings.REDIRECT_URI

            try:
                # Exchange the authorization code for credentials
                flow.fetch_token(code=code)
            except Exception as e:
                logging.error(f"Token exchange failed. Response: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Token exchange error: {str(e)}"
                )

            # Get the ID token from credentials
            try:
                credentials = flow.credentials
                id_info = id_token.verify_oauth2_token(
                    credentials.id_token,
                    requests.Request(),
                    settings.GOOGLE_CLIENT_ID,
                    clock_skew_in_seconds=2
                )
            except Exception as e:
                logging.error(f"Token verification failed: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to verify Google token"
                )

            # Create JWT token
            token = jwt.encode(
                {
                    "sub": id_info["sub"],
                    "email": id_info["email"],
                    "name": id_info.get("name", ""),
                    "exp": datetime.utcnow() + timedelta(days=1)
                },
                settings.JWT_SECRET_KEY,
                algorithm="HS256"
            )

            return {"token": token}

        except HTTPException as he:
            raise he
        except Exception as e:
            logging.error(f"Unexpected error in google_auth: {str(e)}")
            raise HTTPException(status_code=500, detail="Authentication failed")
