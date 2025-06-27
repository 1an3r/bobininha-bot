import os
import json
from typing import Dict

class Database:
    audio_database: Dict[str, str] = {}

    AUDIO_DB_FILE = "audio_database.json"

    def save(self, name, url):
        self.audio_database[name.lower()] = url
        self.persist()

    def load(self):
        try:
            if os.path.exists(self.AUDIO_DB_FILE):
                with open(self.AUDIO_DB_FILE, 'r', encoding='utf-8') as f:
                    self.audio_database = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar banco de dados de áudio: {e}")
            self.audio_database = {}

    def remove(self, name):
        if name not in self.audio_database:
            return

        del self.audio_database[name]

        self.persist()

    def persist(self):
        try:
            with open(self.AUDIO_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.audio_database, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar banco de dados de áudio: {e}")

    def get_all_keys(self):
        return "\n".join([f"• {name}" for name in self.audio_database.keys()])

    def get_database(self):
        return self.audio_database

    def get_database_by(self, key):
        return self.audio_database[key]

    def search_by_name(self, key):
        return

    def __init__(self):
        self.load()