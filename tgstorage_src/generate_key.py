import secrets
import asyncio
import argparse
from database import init_db, verify_key_db
import aiosqlite
from config import settings

async def create_key(owner: str, custom_key: str = None):
    # Ensure DB is initialized
    await init_db()
    
    new_key = custom_key or f"TGSTORAGE-{secrets.token_urlsafe(32)}"
    
    async with aiosqlite.connect(settings.DATABASE_URL) as db:
        try:
            await db.execute(
                "INSERT INTO api_keys (key, owner) VALUES (?, ?)",
                (new_key, owner)
            )
            await db.commit()
            print(f"✅ API Key created successfully for: {owner}")
            print(f"🔑 Key: {new_key}")
            print("⚠️ Save this key safely! It will not be shown again.")
        except aiosqlite.IntegrityError:
            print(f"❌ Error: The key or owner '{owner}' already exists.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate API Keys for TG Storage Cluster")
    parser.add_argument("--owner", required=True, help="Name of the key owner (e.g., 'production_app')")
    parser.add_argument("--key", help="Optional custom key string")
    
    args = parser.parse_args()
    asyncio.run(create_key(args.owner, args.key))
