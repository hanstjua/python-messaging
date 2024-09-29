
from datetime import datetime
import sqlite3
from typing import List

from models import GroupChat, GroupMessage, Message, PrivateMessage, User


CREATE_USER = '''CREATE TABLE IF NOT EXISTS user(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    handle VARCHAR NOT NULL UNIQUE, 
    name VARCHAR NOT NULL
);'''

CREATE_PRIVATE_CHAT = '''CREATE TABLE IF NOT EXISTS private_chat(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    CONSTRAINT fk_user1 FOREIGN KEY (user1_id) REFERENCES user(id) ON DELETE CASCADE,
    CONSTRAINT fk_user2 FOREIGN KEY (user2_id) REFERENCES user(id) ON DELETE CASCADE
);'''

CREATE_GROUP_CHAT = '''CREATE TABLE IF NOT EXISTS group_chat(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE
);'''

CREATE_MESSAGE = '''CREATE TABLE IF NOT EXISTS message(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    content VARCHAR NOT NULL,
    sender_id INTEGER NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified DATETIME,
    CONSTRAINT fk_user FOREIGN KEY (sender_id) REFERENCES user(id) ON DELETE CASCADE
);'''

CREATE_PRIVATE_MESSAGE = '''CREATE TABLE IF NOT EXISTS private_message(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    recipient_id INTEGER NOT NULL,
    private_chat_id INTEGER NOT NULL,
    CONSTRAINT fk_message FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (recipient_id) REFERENCES user(id) ON DELETE CASCADE,
    CONSTRAINT fk_private_chat FOREIGN KEY (private_chat_id) REFERENCES private_chat(id) ON DELETE CASCADE
);'''

CREATE_GROUP_MESSAGE = '''CREATE TABLE IF NOT EXISTS group_message(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    CONSTRAINT fk_message FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE,
    CONSTRAINT fk_group FOREIGN KEY (group_id) REFERENCES group_chat(id) ON DELETE CASCADE
);'''

CREATE_GROUP_MEMBERSHIP = '''CREATE TABLE IF NOT EXISTS group_membership(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    is_admin INTEGER DEFAULT 0,
    CONSTRAINT fk_group FOREIGN KEY (group_id) REFERENCES group_chat(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);'''


class Database:
    def __init__(self) -> None:
        con = sqlite3.connect('database.db')
        con.execute('PRAGMA foreign_keys = ON;')

        # create tables if haven't already
        for command in [CREATE_USER, 
                        CREATE_GROUP_CHAT,
                        CREATE_PRIVATE_CHAT,
                        CREATE_MESSAGE, 
                        CREATE_GROUP_MESSAGE, 
                        CREATE_PRIVATE_MESSAGE, 
                        CREATE_GROUP_MEMBERSHIP]:
             con.execute(command)

    def get_users(self):
        results = sqlite3.connect('database.db').execute('SELECT * FROM user;')

        return results.fetchall()

    def get_user_by_handle(self, handle: str) -> User:
        try:
            result = sqlite3.connect('database.db').execute('SELECT name FROM user WHERE handle = (?);', (handle,))
            name = result.fetchone()[0]

            return None if name is None else User(handle, name)
        except:
            return None
        
    def get_users_in_group_chat(self, group_chat: GroupChat) -> List[User]:
        with sqlite3.connect('database.db') as con:
            rows = con.execute('''SELECT handle, name
FROM user
WHERE user.id IN (SELECT user_id
                  FROM group_membership
                  WHERE group_id = (SELECT id FROM group_chat WHERE name = (?)));''', (group_chat.name,)).fetchall()
            
            return [User(handle=row[0], name=row[1]) for row in rows]
    
    def create_user(self, user: User) -> User:
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            con.execute('INSERT INTO user(handle, name) VALUES (?, ?)', (user.handle, user.name))

        return self.get_user_by_handle(user.handle)
        
    def update_user(self, user: User) -> User:
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            con.execute('UPDATE user SET name = (?) WHERE handle = (?);', (user.name, user.handle))

    def delete_user(self, handle: str):
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            con.execute('DELETE FROM user WHERE handle = (?);', (handle,))
        
    def get_latest_private_messages_by_user(self, user_handle: str) -> List[PrivateMessage]:
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            query = '''SELECT content, timestamp,
(SELECT name FROM user WHERE id = sender_id) as sender_name,
(SELECT handle FROM user WHERE id = sender_id) as sender_handle,
(SELECT name FROM user WHERE id = (SELECT CASE WHEN user1_id = sender_id THEN user2_id ELSE user1_id END)) as recipient_name,
(SELECT handle FROM user WHERE id = (SELECT CASE WHEN user1_id = sender_id THEN user2_id ELSE user1_id END)) as recipient_handle
FROM (SELECT message.content, message.sender_id, MAX(message.created) as timestamp, pm.user1_id, pm.user2_id
      FROM (SELECT private_message.message_id, pc.user1_id, pc.user2_id
            FROM private_message
            INNER JOIN (SELECT id, user1_id, user2_id
                        FROM private_chat
                        WHERE (SELECT id
                               FROM user
                               WHERE handle = (?)) 
                               IN (user1_id, user2_id)) pc
            ON private_message.private_chat_id = pc.id) pm
      INNER JOIN message
      ON message.id = pm.message_id
      GROUP BY user1_id, user2_id);'''
            results = con.execute(query, (user_handle,)).fetchall()

            return [
                PrivateMessage(
                    Message(
                        content,
                        User(
                            sender_handle,
                            sender_name
                        ),
                        datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f'),
                        None
                    ),
                    User(
                        recipient_handle,
                        recipient_name
                    )
                ) for content, timestamp, sender_name, sender_handle, recipient_name, recipient_handle in results
            ]
        
    def get_latest_group_messages_by_user(self, user_handle: str) -> List[GroupMessage]:
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            query = '''SELECT content, timestamp,
(SELECT name FROM user WHERE id = sender_id) as sender_name,
(SELECT handle FROM user WHERE id = sender_id) as sender_handle,
(SELECT name FROM group_chat WHERE id = group_id) as group_name
FROM (SELECT message.content, message.sender_id, MAX(message.created) as timestamp, gm.group_id
      FROM (SELECT group_message.message_id, gmb.user_id, gmb.group_id
            FROM group_message
            INNER JOIN (SELECT id, user_id, group_id
                        FROM group_membership
                        WHERE (SELECT id
                               FROM user
                               WHERE handle = (?)) = user_id) gmb
            ON group_message.group_id = gmb.group_id) gm
      INNER JOIN message
      ON message.id = gm.message_id
      GROUP BY gm.group_id);'''
            results = con.execute(query, (user_handle,)).fetchall()

            return [
                GroupMessage(
                    Message(
                        content,
                        User(
                            sender_handle,
                            sender_name
                        ),
                        datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f'),
                        None
                    ),
                    GroupChat(
                        group_name
                    )
                ) for content, timestamp, sender_name, sender_handle, group_name in results
            ]
        
    def create_private_chat(self, user1_handle: str, user2_handle: str):
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            user1_id = con.execute('SELECT id FROM user WHERE handle = (?);', (user1_handle)).fetchone()[0]
            user2_id = con.execute('SELECT id FROM user WHERE handle = (?);', (user2_handle)).fetchone()[0]

            con.execute('INSERT INTO private_chat(user1_id, user2_id) VALUES (?, ?);', (user1_id, user2_id))
        
    def create_private_message(self, message: Message, recipient: User) -> PrivateMessage:
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            sender_id = con.execute('SELECT id FROM user WHERE handle=(?);', (message.sender.handle,)).fetchone()[0]
            if sender_id is None:
                raise ValueError(f"User '{message.sender.handle}' does not exist.")

            recipient_id = con.execute('SELECT id FROM user WHERE handle=(?);', (recipient.handle,)).fetchone()[0]
            if recipient_id is None:
                raise ValueError(f"User '{recipient}' does not exist.")
            
            cur = con.cursor()
            row = con.execute('SELECT id FROM private_chat WHERE (user1_id = (?) AND user2_id = (?)) OR (user1_id = (?) AND user2_id = (?));',
                                          (sender_id, recipient_id, recipient_id, sender_id)).fetchone()
            if row is None:
                cur.execute('INSERT INTO private_chat(user1_id, user2_id) VALUES (?, ?)', (sender_id, recipient_id))
                private_chat_id = cur.lastrowid
            else:
                private_chat_id = row[0]
            
            cur.execute('INSERT INTO message(content, sender_id, created) VALUES (?, ? ,?);', (message.content, sender_id, message.created))

            message_id = cur.lastrowid

            cur.execute('INSERT INTO private_message(message_id, recipient_id, private_chat_id) VALUES (?, ?, ?);', (message_id, recipient_id, private_chat_id))

    def get_private_messages(self, username1, username2):
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            user1_id, user1_name = con.execute('SELECT id, name FROM user WHERE handle=(?);', (username1,)).fetchone()
            if user1_id is None:
                raise ValueError(f"User '{username1}' does not exist.")
            
            user1 = User(username1, user1_name)
            
            user2_id, user2_name = con.execute('SELECT id, name FROM user WHERE handle=(?);', (username2,)).fetchone()
            if user2_id is None:
                raise ValueError(f"User '{username2}' does not exist.")
            
            user2 = User(username2, user2_name)
            
            query = '''SELECT message.content, message.sender_id, message.created, message.modified
FROM message
INNER JOIN (SELECT message_id
            FROM private_message
            INNER JOIN (SELECT id
                        FROM private_chat
                        WHERE (user1_id = (?) AND user2_id = (?))
                        OR (user1_id = (?) AND user2_id = (?))) pc
           	ON private_message.private_chat_id = pc.id) pm
ON message.id = pm.message_id;'''
            results = con.execute(query, (user1_id, user2_id, user2_id, user1_id)).fetchall()
            
            return [
                PrivateMessage(
                    Message(
                        content,
                        user1 if sender_id == user1_id else user2,
                        datetime.strptime(created, '%Y-%m-%d %H:%M:%S.%f'),
                        datetime.strptime(modified, '%Y-%m-%d %H:%M:%S.%f') if modified else None
                    ),
                    user2 if sender_id == user1_id else user1
                )
                for content, sender_id, created, modified in results
            ]
            
    def create_group_chat(self, group_name: str, member_usernames: List[str]):
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            con.execute('INSERT INTO group_chat(name) VALUES (?)', (group_name,))

            for member in  member_usernames:
                con.execute('''INSERT INTO group_membership(group_id, user_id) VALUES ((SELECT id
                                                                                        FROM group_chat
                                                                                        WHERE name = ?),
                                                                                       (SELECT id
                                                                                        FROM user
                                                                                        WHERE handle = ?))''',
                            (group_name, member))
                
    def get_group_messages(self, group_name: str) -> List[GroupMessage]:
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            results = con.execute('''SELECT user.name, user.handle, m.content, m.created, m.modified
FROM user
INNER JOIN (SELECT message.content, message.sender_id, message.created, message.modified
           	FROM message
           	INNER JOIN (SELECT group_message.message_id
                      	FROM group_message
                       	WHERE group_id = (SELECT id
                                          FROM group_chat
                                          WHERE name = (?))) gc
           	ON gc.message_id = message.id) m
ON m.sender_id = user.id
ORDER BY m.created;''', (group_name,))
            
            return [GroupMessage(
                Message(
                    content=row[2],
                    sender=User(
                        handle=row[1],
                        name=row[0]
                    ),
                    created=datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f'),
                    modified=datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S.%f') if row[4] else None
                ),
                GroupChat(
                    name=group_name
                )
            ) for row in results]
                
    def get_group_chats_by_username(self, username: str) -> List[GroupChat]:
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')
            results = con.execute('''SELECT name
FROM group_chat
WHERE id in (SELECT group_id
            FROM group_membership
            WHERE user_id = (SELECT id
                             FROM user
                             WHERE handle = (?)))''', (username,)).fetchall()
            
            return [GroupChat(name=row[0]) for row in results]
        
    def create_group_message(self, message: Message, group_chat: GroupChat):
        with sqlite3.connect('database.db') as con:
            con.execute('PRAGMA foreign_keys = ON;')

            sender_id = con.execute('SELECT id FROM user WHERE handle=(?);', (message.sender.handle,)).fetchone()[0]
            if sender_id is None:
                raise ValueError(f"User '{message.sender.handle}' does not exist.")

            group_id = con.execute('SELECT id FROM group_chat WHERE name=(?);', (group_chat.name,)).fetchone()[0]
            if group_id is None:
                raise ValueError(f"Group Chat '{group_chat}' does not exist.")
            
            cur = con.cursor()
            cur.execute('INSERT INTO message(content, sender_id, created, modified) VALUES (?,?,?,?);', (
                message.content,
                sender_id,
                message.created,
                message.modified
            ))

            message_id = cur.lastrowid

            cur.execute('INSERT INTO group_message(group_id, message_id) VALUES (?,?);', (group_id, message_id))
