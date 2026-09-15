# Конвертер систем счисления — FastAPI + Vue.js

Перевод чисел между системами счисления (2-36) и арифметика в любой системе.

## Запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск бэкенда (FastAPI)

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Документация API: http://localhost:8000/docs

### 3. Открытие фронтенда

Откройте `frontend/index.html` в браузере (двойной клик по файлу).

## API

| Метод | Эндпоинт          | Назначение                          |
|-------|-------------------|-------------------------------------|
| POST  | `/api/convert`    | Конвертация между системами         |
| POST  | `/api/calculate`  | Арифметика (сложение, вычитание, умножение) |
| POST  | `/api/validate`   | Проверка валидности числа           |
| GET   | `/api/bases`      | Список систем 2-36 с цифрами        |
| GET   | `/api/operations` | Список операций                     |

## Пример API-запроса

```bash
curl -X POST http://localhost:8000/api/convert \
  -H "Content-Type: application/json" \
  -d '{"value": "1010", "from_base": 2, "to_base": 16}'
```

Ответ:
```json
{
  "input_value": "1010",
  "from_base": 2,
  "to_base": 16,
  "result": "A",
  "decimal_value": 10,
  "steps": ["..."]
}
```

## Структура

```
number_systems/
├── backend/
│   └── main.py          # FastAPI приложение
├── frontend/
│   └── index.html       # Vue 3 интерфейс
├── requirements.txt
└── README.md
```# Converter
