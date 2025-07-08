import sqlite3
import os
from datetime import datetime
from classes.Queue import Queue
from classes.Soundboard import Soundboard
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class SQLite3DB:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.DB_PATH = os.path.join(self.BASE_DIR, "bobininha.db")
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
                title      TEXT NOT NULL,
                user       TEXT NOT NULL,
                created_at DATE NOT NULL,
                played     BOOLEAN DEFAULT FALSE
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

    def remove_sound_by_name(self, name: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM soundboard WHERE name = ?",
                       (name.lower(),))
        self.conn.commit()

    def remove_music_by_title(self, title: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM queue WHERE id = (SELECT id FROM queue WHERE title = ? ORDER BY created_at LIMIT 1)", (title,))
        self.conn.commit()

    def get_soundboard_db(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, url, user, created_at FROM soundboard")
        rows = cursor.fetchall()
        return [
            Soundboard(id=row[0], name=row[1], url=row[2],
                       user=row[3], created_at=row[4])
            for row in rows
        ]

    def get_queue(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM queue WHERE played IS FALSE ORDER BY created_at")
        rows = cursor.fetchall()
        return [
            Queue(id=row[0], url=row[1], title=row[2],
                  user=row[3], created_at=row[4])
            for row in rows
        ]

    def append_to_queue(self, url: str, title: str, user: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO queue (url, title, user, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (url, title, user))
        self.conn.commit()

    def count_queue(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM queue WHERE played IS FALSE")
        result = cursor.fetchone()[0]
        return result if result else 0

    def nuking_queue_table(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM queue")
        self.conn.commit()

    def debugging_queue(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE queue SET played = FALSE")
        self.conn.commit()

    def set_played(self, music_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE queue SET played = TRUE WHERE id = ?", (music_id, ))
        logger.debug("Connection inside set_played: %s", cursor.connection)
        self.conn.commit()
