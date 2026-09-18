from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
import re

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="Конвертер систем счисления", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@app.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse("""
    <!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=/app/">
    <title>Системы счисления</title></head>
    <body><p>Загружаю приложение... <a href="/app/">Открыть</a></p></body></html>
    """)


app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="app")


@app.get("/favicon.ico")
def favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
    <rect width="32" height="32" rx="6" fill="#f0db4f"/>
    <text x="16" y="22" font-size="16" font-weight="bold" text-anchor="middle" fill="#1a1a24" font-family="Consolas">B↔H</text>
    </svg>"""
    return Response(content=svg, media_type="image/svg+xml")


class ConvertRequest(BaseModel):
    value: str = Field(..., min_length=1, description="Число для конвертации")
    from_base: int = Field(..., ge=2, le=36, description="Исходная система счисления (2-36)")
    to_base: int = Field(..., ge=2, le=36, description="Целевая система счисления (2-36)")


class ConvertResponse(BaseModel):
    input_value: str
    from_base: int
    to_base: int
    result: str
    decimal_value: int
    steps: list[str]


class ValidateRequest(BaseModel):
    value: str
    base: int = Field(..., ge=2, le=36)


class ValidateResponse(BaseModel):
    valid: bool
    message: str


class BasesInfoResponse(BaseModel):
    base: int
    name: str
    digits: str


def parse_number(value: str, base: int) -> int:
    value = value.strip().upper()
    if not value:
        raise ValueError("Пустое значение")
    neg = False
    if value.startswith("-"):
        neg = True
        value = value[1:]
    if not value:
        raise ValueError("Пустое значение")
    result = 0
    for ch in value:
        idx = VALID_DIGITS.find(ch)
        if idx == -1 or idx >= base:
            raise ValueError(f"Символ '{ch}' недопустим для системы счисления с основанием {base}")
        result = result * base + idx
    return -result if neg else result


def to_base_string(number: int, base: int) -> str:
    if number == 0:
        return "0"
    chars = []
    neg = number < 0
    number = abs(number)
    while number > 0:
        chars.append(VALID_DIGITS[number % base])
        number //= base
    if neg:
        chars.append("-")
    return "".join(reversed(chars))


def build_steps(value: str, from_base: int, to_base: int) -> list[str]:
    steps = []
    value_upper = value.strip().upper()
    decimal = parse_number(value_upper, from_base)
    sign_text = "Отрицательное число (знак −)" if decimal < 0 else "Положительное число"

    steps.append(f"Входное число: {value_upper} (система {from_base})")
    steps.append(f"{sign_text}")

    if from_base == 10:
        steps.append(f"Десятичное значение: {decimal}")
    else:
        steps.append(f"Переводим в десятичную: {decimal}")

    if to_base == 10:
        steps.append(f"Результат в десятичной: {decimal}")
    else:
        n = abs(decimal)
        remainders = []
        while n > 0:
            rem = n % to_base
            remainders.append(f"{n} ÷ {to_base} = {n // to_base}  остаток {rem} ({VALID_DIGITS[rem]})")
            n //= to_base
        steps.append("Делим на основание целевой системы:")
        for r in remainders:
            steps.append(f"  {r}")
        result = to_base_string(decimal, to_base)
        steps.append(f"Читаем остатки снизу вверх → {result}")

    return steps


@app.post("/api/convert", response_model=ConvertResponse)
def convert_number(req: ConvertRequest):
    try:
        value_clean = req.value.strip().upper()
        decimal_val = parse_number(value_clean, req.from_base)
        result = to_base_string(decimal_val, req.to_base)
        steps = build_steps(req.value, req.from_base, req.to_base)
        return ConvertResponse(
            input_value=value_clean,
            from_base=req.from_base,
            to_base=req.to_base,
            result=result,
            decimal_value=decimal_val,
            steps=steps,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/validate", response_model=ValidateResponse)
def validate_number(req: ValidateRequest):
    try:
        parse_number(req.value.strip().upper(), req.base)
        return ValidateResponse(valid=True, message="Число допустимо")
    except ValueError as e:
        return ValidateResponse(valid=False, message=str(e))


@app.get("/api/bases")
def get_bases() -> list[BasesInfoResponse]:
    names = {
        2: "Двоичная", 3: "Троичная", 4: "Четверичная",
        5: "Пятеричная", 6: "Шестеричная", 7: "Семеричная",
        8: "Восьмеричная", 9: "Девятиричная", 10: "Десятичная",
        11: "Одинадцатеричная", 12: "Двенадцатеричная", 16: "Шестнадцатеричная",
        20: "Двадцатеричная", 32: "Тридцатидвухричная", 36: "Тридцатишестеричная",
    }
    result = []
    for b in range(2, 37):
        digits = VALID_DIGITS[:b]
        result.append(BasesInfoResponse(
            base=b,
            name=names.get(b, f"Система с основанием {b}"),
            digits=digits,
        ))
    return result


@app.get("/api/operations")
def get_operations():
    return {
        "operations": [
            {"id": "convert", "name": "Конвертация", "description": "Перевод между системами счисления"},
            {"id": "add", "name": "Сложение", "description": "Сложение двух чисел в указанной системе"},
            {"id": "subtract", "name": "Вычитание", "description": "Вычитание двух чисел в указанной системе"},
            {"id": "multiply", "name": "Умножение", "description": "Умножение двух чисел в указанной системе"},
        ]
    }


class ArithmeticRequest(BaseModel):
    value1: str
    value2: str
    base: int = Field(..., ge=2, le=36)
    operation: str


class ArithmeticResponse(BaseModel):
    value1: str
    value2: str
    base: int
    operation: str
    result_decimal: int
    result: str
    steps: list[str]


@app.post("/api/calculate", response_model=ArithmeticResponse)
def calculate(req: ArithmeticRequest):
    try:
        a = parse_number(req.value1.strip().upper(), req.base)
        b = parse_number(req.value2.strip().upper(), req.base)

        ops = {"add": a + b, "subtract": a - b, "multiply": a * b}
        if req.operation not in ops:
            raise HTTPException(status_code=400, detail=f"Операция '{req.operation}' не поддерживается")

        res = ops[req.operation]
        steps = build_calc_steps(
            req.value1.strip().upper(), req.value2.strip().upper(),
            req.base, req.operation, a, b, res,
        )
        return ArithmeticResponse(
            value1=req.value1.strip().upper(),
            value2=req.value2.strip().upper(),
            base=req.base,
            operation=req.operation,
            result_decimal=res,
            result=to_base_string(res, req.base),
            steps=steps,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def build_calc_steps(value1: str, value2: str, base: int, operation: str, a: int, b: int, res: int) -> list[str]:
    op_symbols = {"add": "+", "subtract": "−", "multiply": "×"}
    symbol = op_symbols.get(operation, operation)
    steps = []

    steps.append(f"Первое число: {value1}")
    steps.append(f"  {value1} (система {base}) = {a} в десятичной")
    steps.append(f"Второе число: {value2}")
    steps.append(f"  {value2} (система {base}) = {b} в десятичной")

    steps.append(f"Операция в десятичной: {a} {symbol} {b} = {res}")

    if base == 10:
        steps.append(f"Результат в десятичной: {res}")
    else:
        n = abs(res)
        remainders = []
        while n > 0:
            rem = n % base
            remainders.append(f"{n} ÷ {base} = {n // base}  остаток {rem} ({VALID_DIGITS[rem]})")
            n //= base
        steps.append("Переводим результат в целевую систему:")
        for r in remainders:
            steps.append(f"  {r}")
        steps.append(f"Читаем остатки снизу вверх → {to_base_string(res, base)} (система {base})")

    return steps
