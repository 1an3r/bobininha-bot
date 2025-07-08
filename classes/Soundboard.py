from dataclasses import dataclass


@dataclass
class Soundboard:
    id: int = 0
    url: str = ""
    name: str = ""
    user: str = ""
    created_at: str = ""
