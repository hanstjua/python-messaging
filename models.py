from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    handle: str
    name: str

@dataclass
class GroupChat:
    name: str

@dataclass
class Message:
    content: str
    sender: User
    created: datetime
    modified: Optional[datetime]

@dataclass
class PrivateMessage:
    message: Message
    recipient: User

@dataclass
class GroupMessage:
    message: Message
    group: GroupChat

@dataclass
class GroupMembership:
    group: GroupChat
    user: User
    is_admin: bool
