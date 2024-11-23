import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    required_vars = [
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_DB',
        'JWT_SECRET_KEY',
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'REDIRECT_URI'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:5432/{os.getenv('POSTGRES_DB')}"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    API_KEY = os.getenv("API_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    CORS_ORIGINS = [
        "http://localhost:3000",
        "https://linguagen.azurewebsites.net",
        "https://linguagen.tech",
        "https://core.linguagen.tech",
    ]

settings = Settings() 