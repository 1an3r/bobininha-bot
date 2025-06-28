import sqlite3
import os
from datetime import datetime

class SQLiteDatabase:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.DB_PATH = os.path.join(self.BASE_DIR, "databobinase.db")
        self.conn = sqlite3.connect(self.DB_PATH)
        self._create_table()

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS soundboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL UNIQUE,
                user TEXT NOT NULL,
                created_at DATE NOT NULL
            );
        """)
        self.conn.commit()

    def save(self, name: str, url: str, user: str):
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO soundboard (name, url, user, created_at)
                VALUES (?, ?, ?, ?)
            """, (name.lower(), url, user, datetime.now().date()))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"[AVISO] '{name}' ou URL já existente no banco.")

    def remove(self, name: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM soundboard WHERE name = ?", (name.lower(),))
        self.conn.commit()

    def get_all_keys(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM soundboard")
        return "\n".join([f"• {row[0]}" for row in cursor.fetchall()])

    def get_all_values(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM soundboard")
        return "\n".join([f".{row[0]}" for row in cursor.fetchall()])

    def get_database(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, url FROM soundboard")
        return {name: url for name, url in cursor.fetchall()}

    def get_by_key(self, key: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM soundboard WHERE name = ?", (key.lower(),))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_by_value(self, value: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM soundboard WHERE url = ?", (value.strip(),))
        return [row[0] for row in cursor.fetchall()]

    def search_by_name(self, key: str):
        return self.get_by_key(key)
