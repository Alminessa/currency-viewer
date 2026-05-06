# database.py - соединение с PosgreSQL и инициализация таблиц

import psycopg2
from psycopg2 import sql
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_connection():         # Соединение с базой данных
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        options='-c client_encoding=UTF8'
    )
    return conn

def init_db():                # Создание таблиц 
    conn = get_connection()
    cur = conn.cursor()

    # Таблица валют (справочник)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS currencies (
            id SERIAL PRIMARY KEY,
            code VARCHAR(3) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL
        )
    """)

    # Таблица курсов (фактические значения на дату)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rates (
                id SERIAL PRIMARY KEY,
                currency_id INT REFERENCES currencies(id) ON DELETE CASCADE,
                rate NUMERIC(12, 4) NOT NULL,
                nominal INT NOT NULL DEFAULT 1,
                date DATE NOT NULL DEFAULT CURRENT_DATE,
                UNIQUE (currency_id, date)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()