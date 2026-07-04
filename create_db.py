import pymysql
from app.config import get_settings

settings = get_settings()

def create_database():
    connection = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME};")
    cursor.execute(f"ALTER DATABASE {settings.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cursor.close()
    connection.close()
    print(f"Database {settings.DB_NAME} ensured.")

if __name__ == "__main__":
    create_database()
