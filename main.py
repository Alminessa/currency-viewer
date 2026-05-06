# main.py - FastApi приложение

from fastapi import FastAPI, Query, HTTPException
from database import init_db
from services import update_rates_in_db, get_today_rates, convert_currency, CurrencyNotFound
from models import CurrencyOut, ConvertOut, MessageOut

app = FastAPI(
    title="CurrencyViewer",
    description="Сервис для просмотра и конвертации валют с использованием API ЦБ РФ",
    version="1.0"
)

@app.on_event("startup")
def startap():
    init_db()
    try:
        update_rates_in_db()
    except Exception as e:
       print(f"Не удалось загрузить начальные курсы: {e}")

@app.get("/", response_model=MessageOut)
def root():
    return {"message": "Добро пожаловать в CurrencyViewer! Перейдите на /docs для документации."}

@app.post("/update", response_model=MessageOut)
def update():
    result = update_rates_in_db()
    return result

@app.get("/rates", response_model=list[CurrencyOut])
def rates():
    return get_today_rates()

@app.get("/convert", response_model=ConvertOut)
def convert(
    from_currency: str = Query(..., alias="from", description="Код валюты, из которой конвертируем (например, USD)"),
    to: str = Query(..., description="Код целевой валюты (например, EUR)"),
    amount: float = Query(..., gt=0, description="Сумма конвертации")
):
    try:
        result = convert_currency(from_currency, to, amount)
        return result
    except CurrencyNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))