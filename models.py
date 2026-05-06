# models.py - модели данных для ответов API

from pydantic import BaseModel, Field

class CurrencyOut(BaseModel):
    code: str
    name: str
    rate: float
    nominal: int

class ConvertOut(BaseModel):
    from_: str = Field(..., alias='from')
    to: str
    amount: float
    result: float

    class Config:
        populate_by_name = True

class MessageOut(BaseModel):
    message: str