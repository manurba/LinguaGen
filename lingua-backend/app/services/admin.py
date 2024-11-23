from app.core.database import get_db_connection

class AdminService:
    async def get_all_users(self):
        conn = await get_db_connection()
        users = await conn.fetch('SELECT * FROM users ORDER BY created_at DESC')
        await conn.close()
        return [dict(user) for user in users]
    
    async def add_to_whitelist(self, email: str):
        conn = await get_db_connection()
        try:
            await conn.execute(
                'INSERT INTO whitelist (email) VALUES ($1)',
                email
            )
            return {"message": f"Added {email} to whitelist"}
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error adding to whitelist: {str(e)}"
            )
        finally:
            await conn.close()
