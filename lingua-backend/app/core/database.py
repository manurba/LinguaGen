import asyncpg
from app.core.config import settings

async def init_db():
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        # Create whitelist table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS whitelist (
                email TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                google_id TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create conversations table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                email TEXT REFERENCES users(email),
                messages TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create whitelist_requests table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS whitelist_requests (
                email TEXT PRIMARY KEY,
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
    finally:
        await conn.close()

async def get_db_connection():
    return await asyncpg.connect(settings.DATABASE_URL)