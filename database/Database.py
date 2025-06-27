import os
import json
from typing import Dict

class Database:
    audio_database: Dict[str, str] = {}

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    AUDIO_DB_FILE = os.path.join(BASE_DIR, "audio_database.json")

    def __init__(self):
        self._ensure_db_directory_exists()
        self.load()

    def _ensure_db_directory_exists(self):
        """Ensures the database directory exists. Creates it if it doesn't."""
        if not os.path.exists(self.BASE_DIR):
            os.makedirs(self.BASE_DIR, exist_ok=True) # exist_ok=True prevents an error if the directory already exists

    def save(self, name, url):
        self.audio_database[name.lower()] = url
        self.persist()

    def load(self):
        try:
            if os.path.exists(self.AUDIO_DB_FILE):
                with open(self.AUDIO_DB_FILE, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    if file_content:
                        self.audio_database = json.loads(file_content)
                    else:
                        self.audio_database = {}
            else:
                self.audio_database = {}
                self.persist()
        except json.JSONDecodeError:
            print(f"Warning: {self.AUDIO_DB_FILE} is empty or corrupted. Initializing empty database.")
            self.audio_database = {}
            self.persist()
        except Exception as e:
            print(f"Erro ao carregar banco de dados de áudio: {e}")
            self.audio_database = {}
            self.persist()

    def remove(self, name):
        if name.lower() not in self.audio_database:
            return

        del self.audio_database[name.lower()]

        self.persist()

    def persist(self):
        try:
            with open(self.AUDIO_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.audio_database, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar banco de dados de áudio: {e}")

    def get_all_keys(self):
        return "\n".join([f"• {name}" for name in self.audio_database.keys()])

    def get_all_values(self):
        return "\n".join([f".{url}" for url in self.audio_database.values()])

    def get_database(self):
        return self.audio_database

    def get_database_by(self, key):
        return self.audio_database.get(key.lower())

    def search_by_name(self, key):
        return self.audio_database.get(key.lower())