from dataclasses import dataclass


@dataclass
class Queue:
    id: int = 0
    url: str = ""
    title: str = ""
    user: str = ""
    created_at: str = ""