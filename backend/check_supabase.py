import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, engine
from app.core.config import settings

async def check():
    print(f"SUPABASE_URL={settings.supabase_url}")
    print(f"DATABASE_URL={settings.database_url[:50]}...")
    print(f"project_ref=suhfzwsznboqnjkpwfho")
    async with AsyncSessionLocal() as db:
        for tbl in ['payers','providers','patients','claims','denials','payments','work_queues','users','agent_runs','claim_queue_assignments']:
            try:
                r=await db.execute(text(f'SELECT count(*) FROM {tbl}'))
                cnt=r.scalar()
                print(f"{tbl}: {cnt} rows")
            except Exception as e:
                print(f"{tbl}: ERROR {e}")
        try:
            r=await db.execute(text("SELECT current_database()"))
            print("current_database:", r.scalar())
        except Exception as e:
            print("db info error", e)
        r=await db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"))
        print("public tables:", [row[0] for row in r.fetchall()])

asyncio.run(check())