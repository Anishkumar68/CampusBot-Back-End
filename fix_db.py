# fix_roles.py
import os
import psycopg2

from dotenv import load_dotenv

load_dotenv()


def fix_bot_roles():
    # Use your Render external database URL
    DATABASE_URL = os.getenv("DATABASE_URL")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Update roles
    cursor.execute("UPDATE chat_messages SET role = 'assistant' WHERE role = 'bot';")
    updated_count = cursor.rowcount

    conn.commit()
    print(f"Updated {updated_count} records from 'bot' to 'assistant'")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    fix_bot_roles()
