import sqlite3
from config import DB_NAME

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ip TEXT,
            port INTEGER,
            username TEXT,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vpn_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            server_id INTEGER, 
            username TEXT,
            traffic_limit TEXT,
            days INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
def add_server(user_id, ip, port, username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO servers (user_id, ip, port, username, password) VALUES (?, ?, ?, ?, ?)", 
                   (user_id, ip, port, username, password))
    conn.commit()
    server_id = cursor.lastrowid
    conn.close()
    return server_id

def get_user_servers(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, ip, port, username, password FROM servers WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    # Artık root yerine veritabanındaki username'i çekiyoruz
    return [{"id": r[0], "ip": r[1], "port": r[2], "user": r[3], "pass": r[4]} for r in rows]

def get_server_by_id(server_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, ip, port, username, password FROM servers WHERE id = ?", (server_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "ip": row[1], "port": row[2], "user": row[3], "pass": row[4]}
    return None

def delete_server(server_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    cursor.execute("DELETE FROM vpn_users WHERE server_id = ?", (server_id,))
    conn.commit()
    conn.close()

# --- VPN KULLANICI İŞLEMLERİ ---
def add_vpn_user(admin_id, server_id, username, traffic, days):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vpn_users (admin_id, server_id, username, traffic_limit, days) VALUES (?, ?, ?, ?, ?)", 
                   (admin_id, server_id, username, traffic, days))
    conn.commit()
    conn.close()

def get_vpn_users(server_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, traffic_limit, days FROM vpn_users WHERE server_id = ?", (server_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_vpn_user(server_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vpn_users WHERE server_id = ? AND username = ?", (server_id, username))
    conn.commit()
    conn.close()

def update_vpn_user(server_id, username, new_traffic, new_days):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE vpn_users SET traffic_limit = ?, days = ? WHERE server_id = ? AND username = ?", 
                   (new_traffic, new_days, server_id, username))
    conn.commit()
    conn.close()

init_db()
