# services.py - работа с внешним API и обработка данных

import requests
import json
from datetime import date
from database import get_connection
from config import CBR_API_URL

def fetch_cbr_rates():              # Актуальные курсы валют ЦБ РФ
    response = requests.get(CBR_API_URL)
    response.raise_for_status()
    response.encoding = 'utf-8'

    text = response.text
    if text.startswith('\ufeff'):
        text = text[1:]
    
    data = response.json()

    valutes = data.get("Valute", {})
    rates = {}
    for char_code, info in valutes.items():
        nominal = info.get("Nominal", 1)
        value = info.get("Value", 0)

        rate_per_unit = value / nominal
        rates[char_code] = {
            "name": info.get("Name", char_code),
            "rate": round(rate_per_unit, 4),
            "nominal": nominal
        }
    return rates

def update_rates_in_db():           # Сохранение актуальных курсов в БД
    rates = fetch_cbr_rates()
    today = date.today()

    rates['RUB'] = {
        "name": "Российский рубль",
        "rate": 1.0,
        "nominal": 1
    }
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM exchange_rates WHERE date = %s", (today,))

    for code, info in rates.items():
        cur.execute("SELECT id FROM currencies WHERE code = %s", (code,))
        row = cur.fetchone()
        if row:
            currency_id = row[0]
        else:
            cur.execute(
                "INSERT INTO currencies (code, name) VALUES (%s, %s) RETURNING id",
                (code, info["name"])
            )
            currency_id = cur.fetchone()[0]
        
        cur.execute(
            "INSERT INTO exchange_rates (currency_id, rate, nominal, date)"
            "VALUES (%s, %s, %s, %s)",
            (currency_id, info["rate"], info["nominal"], today)
        )
    
    conn.commit()
    cur.close()
    conn.close()
    return {"message": f"Курсы на {today} успешно обновлены"}

def get_today_rates():              # Курсы на сегодняшний день из БД
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.code, c.name, er.rate, er.nominal
        FROM exchange_rates er
        JOIN currencies c ON er.currency_id = c.id
        WHERE er.date = %s
        ORDER BY c.code
    """, (today,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    rates = []
    for code, name, rate, nominal in rows:
        rates.append({
            "code": code,
            "name": name,
            "rate": float(rate),
            "nominal": nominal
        })
    return rates

class CurrencyNotFound(Exception):
    pass

def convert_currency(from_code: str, to_code: str, amount: float):              # Конвертация суммы из одной валюты в другую через рубль
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT er.rate, er.nominal
        FROM exchange_rates er
        JOIN currencies c ON er.currency_id = c.id
        WHERE c.code = %s AND er.date = %s
    """, (from_code.upper(), today))
    from_row = cur.fetchone()
    if not from_row:
        cur.close()
        conn.close()
        raise CurrencyNotFound(f"Валюта {from_code} не найдена на {today}")
    
    cur.execute("""
        SELECT er.rate, er.nominal
        FROM exchange_rates er
        JOIN currencies c ON er.currency_id = c.id
        WHERE c.code = %s AND er.date = %s
    """, (to_code.upper(), today))
    to_row = cur.fetchone()
    if not to_row:
        cur.slose()
        conn.close()
        raise CurrencyNotFound(f"Валюта {to_code} не найдена на {today}")
    
    from_rate = float(from_row[0]) / from_row[1]
    to_rate = float(to_row[0]) / to_row[1]

    rub_amount = amount * from_rate
    result = rub_amount / to_rate

    cur.close()
    conn.close()

    return {
        "from": from_code.upper(),
        "to": to_code.upper(),
        "amount": amount,
        "result": round(result, 2)
    }