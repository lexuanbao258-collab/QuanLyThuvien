import psycopg2
from config import DB_CONFIG

def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SET search_path TO thu_vien;")
    cur.close()
    return conn
