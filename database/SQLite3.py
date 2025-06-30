import sqlite3
import os
from datetime import datetime

class SQLite3DB:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.DB_PATH = os.path.join(self.BASE_DIR, "databobinase.db")
        self.conn = sqlite3.connect(self.DB_PATH)
        self._create_queue_table()
        self._create_soundboard_table()

    def _create_soundboard_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS soundboard (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL UNIQUE,
                url        TEXT NOT NULL UNIQUE,
                user       TEXT NOT NULL,
                created_at DATE NOT NULL
            );
        """)
        self.conn.commit()

    def _create_queue_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                url        TEXT NOT NULL,
                user       TEXT NOT NULL,
                created_at DATE NOT NULL
            );
        """)
        self.conn.commit()

    def save_sound(self, name: str, url: str, user: str):
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO soundboard (name, url, user, created_at)
                VALUES (?, ?, ?, ?)
            """, (name.lower(), url, user, datetime.now().date()))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"[AVISO] '{name}' ou URL já existente no banco.")

    def remove_sound(self, name: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM soundboard WHERE name = ?", (name.lower(),))
        self.conn.commit()

    def remove_music(self, url: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM queue WHERE url = ?", (url,))
        self.conn.commit()

    def get_all_sound_names(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM soundboard")
        return "\n".join([f"• {row[0]}" for row in cursor.fetchall()])

    def get_all_sound_urls(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM soundboard")
        return "\n".join([f".{row[0]}" for row in cursor.fetchall()])

    def get_all_music_urls(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM queue")
        return "\n".join([f".{row[0]}" for row in cursor.fetchall()])

    def get_soundboard_db(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, url FROM soundboard")
        return {name: url for name, url in cursor.fetchall()}

    def get_queue_columns(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url, user, created_at FROM queue")
        rows = cursor.fetchall()
        return [
            {"url": url, "user": user, "created_at": created_at.split(" ")[0]}
            for url, user, created_at in rows
        ]

    def get_soundboard_db_columns(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, url, user, created_at FROM soundboard")
        rows = cursor.fetchall()
        return [
            {"name": name, "url": url, "user": user, "created_at": created_at.split(" ")[0]}
            for name, url, user, created_at in rows
        ]

    def get_sound_by_name(self, name: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM soundboard WHERE name = ?", (name.lower(),))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_sound_by_url(self, url: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM soundboard WHERE url = ?", (url.strip(),))
        return [row[0] for row in cursor.fetchall()]

    def get_current_queue_music(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM queue ORDER BY created_at LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None

    def append_to_queue(self, url: str, user: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO queue (url, user, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (url, user))
        self.conn.commit()

    def remove_current_music(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM queue WHERE id = (SELECT id FROM queue ORDER BY created_at LIMIT 1)")
        self.conn.commit()

    def count_queue(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM queue")
        return cursor.fetchone()[0] if cursor.fetchone() else None

    def get_queue(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url, user FROM queue ORDER BY created_at")
        return [{"url": row[0], "user": row[1]} for row in cursor.fetchall()]