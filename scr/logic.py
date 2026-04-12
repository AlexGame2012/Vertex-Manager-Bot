import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_file="vertex_bot.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_tables()
    
    def _init_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS moderators (
                chat_id INTEGER,
                user_id INTEGER,
                rank INTEGER DEFAULT 0,
                assigned_by INTEGER,
                assigned_at TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bans (
                chat_id INTEGER,
                user_id INTEGER,
                until TIMESTAMP,
                reason TEXT,
                moderator_id INTEGER,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mutes (
                chat_id INTEGER,
                user_id INTEGER,
                until TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                until TIMESTAMP,
                reason TEXT,
                moderator_id INTEGER
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                warn_limit INTEGER DEFAULT 3,
                warn_ban_period TEXT DEFAULT '7d',
                warn_storage_period TEXT DEFAULT '30d',
                default_mute_period TEXT DEFAULT '7d',
                welcome_msg TEXT,
                rules TEXT,
                chat_link TEXT,
                is_closed INTEGER DEFAULT 0,
                antispam INTEGER DEFAULT 1
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS farm (
                chat_id INTEGER,
                user_id INTEGER,
                last_farm TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS nicknames (
                chat_id INTEGER,
                user_id INTEGER,
                nickname TEXT,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS titles (
                chat_id INTEGER,
                user_id INTEGER,
                title TEXT,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                gender TEXT,
                city TEXT,
                birthday TEXT,
                about TEXT,
                motto TEXT,
                is_visible INTEGER DEFAULT 1
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages_stats (
                chat_id INTEGER,
                user_id INTEGER,
                date DATE,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id, date)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vertexes (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands_access (
                chat_id INTEGER,
                command TEXT,
                min_rank INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, command)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                to_user INTEGER,
                from_user INTEGER,
                gift_type TEXT,
                gift_date TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def save_user(self, user_id, username=None, first_name=None, last_name=None):
        now = datetime.now()
        self.cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if self.cursor.fetchone():
            self.cursor.execute("UPDATE users SET username=?, first_name=?, last_name=?, last_seen=? WHERE user_id=?",
                               (username, first_name, last_name, now, user_id))
        else:
            self.cursor.execute("INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen) VALUES (?,?,?,?,?,?)",
                               (user_id, username, first_name, last_name, now, now))
        self.conn.commit()
    
    def get_user(self, user_id):
        self.cursor.execute("SELECT user_id, username, first_name, last_name, first_seen, last_seen FROM users WHERE user_id=?", (user_id,))
        return self.cursor.fetchone()
    
    def get_user_by_username(self, username):
        self.cursor.execute("SELECT user_id, username, first_name, last_name FROM users WHERE username LIKE ?", (f"%{username}%",))
        return self.cursor.fetchone()
    
    def get_moder_rank(self, chat_id, user_id):
        self.cursor.execute("SELECT rank FROM moderators WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = self.cursor.fetchone()
        return row[0] if row else 0
    
    def set_moder_rank(self, chat_id, user_id, rank, assigned_by):
        self.cursor.execute("INSERT OR REPLACE INTO moderators (chat_id, user_id, rank, assigned_by, assigned_at) VALUES (?,?,?,?,?)",
                           (chat_id, user_id, rank, assigned_by, datetime.now()))
        self.conn.commit()
    
    def remove_moder(self, chat_id, user_id):
        self.cursor.execute("DELETE FROM moderators WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        self.conn.commit()
    
    def get_all_moders(self, chat_id):
        self.cursor.execute("SELECT user_id, rank FROM moderators WHERE chat_id=? ORDER BY rank DESC", (chat_id,))
        return self.cursor.fetchall()
    
    def ban_user(self, chat_id, user_id, until, reason, moderator_id):
        self.cursor.execute("INSERT OR REPLACE INTO bans (chat_id, user_id, until, reason, moderator_id) VALUES (?,?,?,?,?)",
                           (chat_id, user_id, until, reason, moderator_id))
        self.conn.commit()
    
    def unban_user(self, chat_id, user_id):
        self.cursor.execute("DELETE FROM bans WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        self.conn.commit()
    
    def is_banned(self, chat_id, user_id):
        self.cursor.execute("SELECT until FROM bans WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = self.cursor.fetchone()
        if row:
            until = datetime.fromisoformat(row[0])
            if until > datetime.now():
                return True
            else:
                self.unban_user(chat_id, user_id)
        return False
    
    def get_ban_reason(self, chat_id, user_id):
        self.cursor.execute("SELECT reason, moderator_id FROM bans WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        return self.cursor.fetchone()
    
    def mute_user(self, chat_id, user_id, until):
        self.cursor.execute("INSERT OR REPLACE INTO mutes (chat_id, user_id, until) VALUES (?,?,?)",
                           (chat_id, user_id, until))
        self.conn.commit()
    
    def unmute_user(self, chat_id, user_id):
        self.cursor.execute("DELETE FROM mutes WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        self.conn.commit()
    
    def is_muted(self, chat_id, user_id):
        self.cursor.execute("SELECT until FROM mutes WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = self.cursor.fetchone()
        if row:
            until = datetime.fromisoformat(row[0])
            if until > datetime.now():
                return True
            else:
                self.unmute_user(chat_id, user_id)
        return False
    
    def get_user_active_mutes(self, user_id):
        self.cursor.execute("SELECT chat_id, until FROM mutes WHERE user_id=? AND until > ?", (user_id, datetime.now()))
        return self.cursor.fetchall()
    
    def add_warn(self, chat_id, user_id, until, reason, moderator_id):
        self.cursor.execute("INSERT INTO warns (chat_id, user_id, until, reason, moderator_id) VALUES (?,?,?,?,?)",
                           (chat_id, user_id, until, reason, moderator_id))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_user_warns(self, chat_id, user_id):
        self.cursor.execute("SELECT id, until, reason, moderator_id FROM warns WHERE chat_id=? AND user_id=? AND until > ?",
                           (chat_id, user_id, datetime.now()))
        return self.cursor.fetchall()
    
    def remove_warn(self, warn_id):
        self.cursor.execute("DELETE FROM warns WHERE id=?", (warn_id,))
        self.conn.commit()
    
    def remove_all_warns(self, chat_id, user_id):
        self.cursor.execute("DELETE FROM warns WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        self.conn.commit()
    
    def get_warn_limit(self, chat_id):
        self.cursor.execute("SELECT warn_limit FROM chat_settings WHERE chat_id=?", (chat_id,))
        row = self.cursor.fetchone()
        return row[0] if row else 3
    
    def get_chat_setting(self, chat_id, setting):
        try:
            self.cursor.execute(f"SELECT {setting} FROM chat_settings WHERE chat_id=?", (chat_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except:
            return None
    
    def set_chat_setting(self, chat_id, setting, value):
        self.cursor.execute(f"INSERT OR REPLACE INTO chat_settings (chat_id, {setting}) VALUES (?,?)", (chat_id, value))
        self.conn.commit()
    
    def get_last_farm(self, chat_id, user_id):
        self.cursor.execute("SELECT last_farm FROM farm WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = self.cursor.fetchone()
        return datetime.fromisoformat(row[0]) if row else None
    
    def set_last_farm(self, chat_id, user_id):
        self.cursor.execute("INSERT OR REPLACE INTO farm (chat_id, user_id, last_farm) VALUES (?,?,?)",
                           (chat_id, user_id, datetime.now()))
        self.conn.commit()
    
    def set_nickname(self, chat_id, user_id, nickname):
        self.cursor.execute("INSERT OR REPLACE INTO nicknames (chat_id, user_id, nickname) VALUES (?,?,?)",
                           (chat_id, user_id, nickname))
        self.conn.commit()
    
    def get_nickname(self, chat_id, user_id):
        self.cursor.execute("SELECT nickname FROM nicknames WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def remove_nickname(self, chat_id, user_id):
        self.cursor.execute("DELETE FROM nicknames WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        self.conn.commit()
    
    def set_title(self, chat_id, user_id, title):
        self.cursor.execute("INSERT OR REPLACE INTO titles (chat_id, user_id, title) VALUES (?,?,?)",
                           (chat_id, user_id, title))
        self.conn.commit()
    
    def get_title(self, chat_id, user_id):
        self.cursor.execute("SELECT title FROM titles WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def set_profile(self, user_id, field, value):
        self.cursor.execute("SELECT user_id FROM profiles WHERE user_id=?", (user_id,))
        if self.cursor.fetchone():
            self.cursor.execute(f"UPDATE profiles SET {field}=? WHERE user_id=?", (value, user_id))
        else:
            self.cursor.execute(f"INSERT INTO profiles (user_id, {field}) VALUES (?,?)", (user_id, value))
        self.conn.commit()
    
    def get_profile(self, user_id):
        self.cursor.execute("SELECT gender, city, birthday, about, motto, is_visible FROM profiles WHERE user_id=?", (user_id,))
        return self.cursor.fetchone()
    
    def add_message(self, chat_id, user_id):
        today = datetime.now().date()
        self.cursor.execute("INSERT INTO messages_stats (chat_id, user_id, date, count) VALUES (?,?,?,1) "
                           "ON CONFLICT(chat_id, user_id, date) DO UPDATE SET count = count + 1",
                           (chat_id, user_id, today))
        self.conn.commit()
    
    def get_user_stats(self, chat_id, user_id, days=30):
        start_date = datetime.now().date() - timedelta(days=days)
        self.cursor.execute("SELECT date, count FROM messages_stats WHERE chat_id=? AND user_id=? AND date >= ? ORDER BY date",
                           (chat_id, user_id, start_date))
        return self.cursor.fetchall()
    
    def get_vertexes(self, user_id):
        self.cursor.execute("SELECT balance FROM vertexes WHERE user_id=?", (user_id,))
        row = self.cursor.fetchone()
        return row[0] if row else 0
    
    def get_top_vertexes(self, limit=10):
        self.cursor.execute("SELECT user_id, balance FROM vertexes ORDER BY balance DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()
    
    def add_vertexes(self, user_id, amount):
        self.cursor.execute("INSERT INTO vertexes (user_id, balance) VALUES (?,?) "
                           "ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?",
                           (user_id, amount, amount))
        self.conn.commit()
    
    def transfer_vertexes(self, from_user, to_user, amount):
        if self.get_vertexes(from_user) >= amount:
            self.add_vertexes(from_user, -amount)
            self.add_vertexes(to_user, amount)
            return True
        return False
    
    def add_gift(self, to_user, from_user, gift_type, gift_date):
        self.cursor.execute("INSERT INTO gifts (to_user, from_user, gift_type, gift_date) VALUES (?,?,?,?)",
                           (to_user, from_user, gift_type, gift_date))
        self.conn.commit()
    
    def get_user_gifts(self, user_id):
        self.cursor.execute("SELECT id, from_user, gift_type, gift_date FROM gifts WHERE to_user=? ORDER BY gift_date DESC", (user_id,))
        return self.cursor.fetchall()
    
    def remove_self_mute(self, chat_id, user_id):
        return False
    
    def get_chat_stats_period(self, chat_id, days):
        start_date = datetime.now().date() - timedelta(days=days)
        self.cursor.execute("SELECT user_id, SUM(count) as total FROM messages_stats WHERE chat_id=? AND date >= ? GROUP BY user_id ORDER BY total DESC LIMIT 10",
                           (chat_id, start_date))
        return self.cursor.fetchall()
    
    def get_command_min_rank(self, chat_id, command):
        self.cursor.execute("SELECT min_rank FROM commands_access WHERE chat_id=? AND command=?", (chat_id, command))
        row = self.cursor.fetchone()
        return row[0] if row else 0
    
    def set_command_access(self, chat_id, command, min_rank):
        self.cursor.execute("INSERT OR REPLACE INTO commands_access (chat_id, command, min_rank) VALUES (?,?,?)",
                           (chat_id, command, min_rank))
        self.conn.commit()

db = Database()