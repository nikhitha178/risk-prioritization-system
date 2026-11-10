from sqlalchemy import text
from backend.app.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("PostgreSQL connection successful!")
        print(result.fetchone()[0])

except Exception as error:
    print("Database connection failed!")
    print(error)
