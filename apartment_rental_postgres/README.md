# Оренда квартир — FastAPI проєкт

Навчальний вебзастосунок для предметної області **"Оренда квартир"**.

## Що реалізовано

- FastAPI
- серверна генерація HTML через Jinja2
- SQLite
- SQLAlchemy ORM
- ролі: `admin` та `user`
- CRUD для сутності `Apartment`
- REST API для квартир

## Сутності

- Client
- Landlord
- City
- Apartment
- Deal

## Запуск

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Відкрити в браузері:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/?role=user`
- `http://127.0.0.1:8000/?role=admin`

## CRUD для квартир

- Створення: `/apartments/create?role=admin`
- Перегляд: `/apartments?role=admin` або `/apartments?role=user`
- Редагування: `/apartments/{id}/edit?role=admin`
- Видалення: `/apartments/{id}/delete?role=admin`

## API

- `GET /api/apartments`
- `GET /api/apartments/{id}`
- `POST /api/apartments`
- `PUT /api/apartments/{id}`
- `DELETE /api/apartments/{id}`
