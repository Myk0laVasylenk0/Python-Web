from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import City, Landlord, Client, Apartment, Deal

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Система оренди квартир API",
    summary="Навчальний REST API для предметної області 'Оренда квартир'",
    description="""
API для вебзастосунку з серверною генерацією HTML та роботою з базою даних SQLite.

## Основні можливості:
- перегляд квартир
- CRUD для квартир
- перегляд міст, клієнтів, орендодавців
- створення угод оренди

## Ролі:
- **admin** — може створювати, редагувати та видаляти квартири
- **user** — може переглядати інформацію та створювати угоди
""",
    version="1.0.0",
    docs_url="/documentation",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
        "docExpansion": "list",
    },
    openapi_tags=[
        {"name": "Pages", "description": "HTML-сторінки вебзастосунку"},
        {"name": "Apartments API", "description": "REST API для роботи з квартирами"},
        {"name": "Deals", "description": "Операції, пов’язані з угодами оренди"},
        {"name": "Reference", "description": "Довідкові сторінки: міста, клієнти, орендодавці"},
    ],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_role(request: Request) -> str:
    role = request.query_params.get("role", "user")
    if role not in ["admin", "user"]:
        return "user"
    return role


def seed_data(db: Session):
    if db.query(City).count() == 0:
        kyiv = City(name="Київ")
        lviv = City(name="Львів")
        db.add_all([kyiv, lviv])
        db.commit()

    if db.query(Landlord).count() == 0:
        l1 = Landlord(full_name="Іван Петренко", phone="+380501111111")
        l2 = Landlord(full_name="Олена Коваль", phone="+380502222222")
        db.add_all([l1, l2])
        db.commit()

    if db.query(Client).count() == 0:
        c1 = Client(full_name="Марія Іваненко", phone="+380503333333")
        c2 = Client(full_name="Олексій Бондар", phone="+380504444444")
        db.add_all([c1, c2])
        db.commit()

    if db.query(Apartment).count() == 0:
        city1 = db.query(City).filter(City.name == "Київ").first()
        city2 = db.query(City).filter(City.name == "Львів").first()
        landlord1 = db.query(Landlord).filter(Landlord.full_name == "Іван Петренко").first()
        landlord2 = db.query(Landlord).filter(Landlord.full_name == "Олена Коваль").first()

        a1 = Apartment(
            title="1-кімнатна квартира біля метро",
            address="вул. Хрещатик, 10",
            rooms=1,
            price=12000,
            status="available",
            city_id=city1.id,
            landlord_id=landlord1.id,
        )
        a2 = Apartment(
            title="2-кімнатна квартира в центрі",
            address="просп. Свободи, 15",
            rooms=2,
            price=18000,
            status="available",
            city_id=city2.id,
            landlord_id=landlord2.id,
        )
        db.add_all([a1, a2])
        db.commit()


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    seed_data(db)
    db.close()


@app.get(
    "/",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Головна сторінка",
    description="Повертає головну HTML-сторінку системи оренди квартир.",
)
def home(request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    apartments = db.query(Apartment).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "role": role,
            "apartments": apartments,
        },
    )


@app.get(
    "/apartments",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Список квартир",
    description="Повертає HTML-сторінку зі списком усіх квартир.",
)
def apartment_list(request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    apartments = db.query(Apartment).all()
    return templates.TemplateResponse(
        "apartments.html",
        {
            "request": request,
            "role": role,
            "apartments": apartments,
        },
    )


@app.get(
    "/apartments/create",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Сторінка створення квартири",
    description="Повертає HTML-форму для створення нової квартири.",
)
def apartment_create_page(request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може створювати квартири")

    cities = db.query(City).all()
    landlords = db.query(Landlord).all()

    return templates.TemplateResponse(
        "apartment_form.html",
        {
            "request": request,
            "role": role,
            "cities": cities,
            "landlords": landlords,
            "apartment": None,
        },
    )


@app.post(
    "/apartments/create",
    tags=["Pages"],
    summary="Створити квартиру",
    description="Обробляє HTML-форму та створює нову квартиру.",
)
def apartment_create(
    request: Request,
    title: str = Form(...),
    address: str = Form(...),
    rooms: int = Form(...),
    price: int = Form(...),
    city_id: int = Form(...),
    landlord_id: int = Form(...),
    db: Session = Depends(get_db),
):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може створювати квартири")

    apartment = Apartment(
        title=title,
        address=address,
        rooms=rooms,
        price=price,
        city_id=city_id,
        landlord_id=landlord_id,
        status="available",
    )
    db.add(apartment)
    db.commit()

    return RedirectResponse(url=f"/apartments?role={role}", status_code=303)


@app.get(
    "/apartments/{apartment_id}/edit",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Сторінка редагування квартири",
    description="Повертає HTML-форму для редагування квартири за її ID.",
)
def apartment_edit_page(apartment_id: int, request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може редагувати квартири")

    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    cities = db.query(City).all()
    landlords = db.query(Landlord).all()

    return templates.TemplateResponse(
        "apartment_form.html",
        {
            "request": request,
            "role": role,
            "cities": cities,
            "landlords": landlords,
            "apartment": apartment,
        },
    )


@app.post(
    "/apartments/{apartment_id}/edit",
    tags=["Pages"],
    summary="Оновити квартиру",
    description="Обробляє HTML-форму та оновлює квартиру за її ID.",
)
def apartment_edit(
    apartment_id: int,
    request: Request,
    title: str = Form(...),
    address: str = Form(...),
    rooms: int = Form(...),
    price: int = Form(...),
    status: str = Form(...),
    city_id: int = Form(...),
    landlord_id: int = Form(...),
    db: Session = Depends(get_db),
):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може редагувати квартири")

    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    apartment.title = title
    apartment.address = address
    apartment.rooms = rooms
    apartment.price = price
    apartment.status = status
    apartment.city_id = city_id
    apartment.landlord_id = landlord_id

    db.commit()
    return RedirectResponse(url=f"/apartments?role={role}", status_code=303)


@app.post(
    "/apartments/{apartment_id}/delete",
    tags=["Pages"],
    summary="Видалити квартиру",
    description="Видаляє квартиру за її ID через HTML-інтерфейс.",
)
def apartment_delete(apartment_id: int, request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може видаляти квартири")

    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    db.delete(apartment)
    db.commit()
    return RedirectResponse(url=f"/apartments?role={role}", status_code=303)


@app.get(
    "/cities",
    response_class=HTMLResponse,
    tags=["Reference"],
    summary="Список міст",
    description="Повертає HTML-сторінку зі списком міст.",
)
def city_list(request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    cities = db.query(City).all()
    return templates.TemplateResponse(
        "cities.html",
        {
            "request": request,
            "role": role,
            "cities": cities,
        },
    )


@app.get(
    "/landlords",
    response_class=HTMLResponse,
    tags=["Reference"],
    summary="Список орендодавців",
    description="Повертає HTML-сторінку зі списком орендодавців.",
)
def landlord_list(request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    landlords = db.query(Landlord).all()
    return templates.TemplateResponse(
        "landlords.html",
        {
            "request": request,
            "role": role,
            "landlords": landlords,
        },
    )


@app.get(
    "/clients",
    response_class=HTMLResponse,
    tags=["Reference"],
    summary="Список клієнтів",
    description="Повертає HTML-сторінку зі списком клієнтів.",
)
def client_list(request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    clients = db.query(Client).all()
    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "role": role,
            "clients": clients,
        },
    )


@app.get(
    "/deals",
    response_class=HTMLResponse,
    tags=["Deals"],
    summary="Список угод",
    description="Повертає HTML-сторінку зі списком угод оренди.",
)
def deal_list(request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    deals = db.query(Deal).all()
    return templates.TemplateResponse(
        "deals.html",
        {
            "request": request,
            "role": role,
            "deals": deals,
        },
    )


@app.get(
    "/deals/create",
    response_class=HTMLResponse,
    tags=["Deals"],
    summary="Сторінка створення угоди",
    description="Повертає HTML-форму для створення нової угоди оренди.",
)
def deal_create_page(request: Request, db: Session = Depends(get_db)):
    role = get_role(request)
    apartments = db.query(Apartment).filter(Apartment.status == "available").all()
    clients = db.query(Client).all()

    return templates.TemplateResponse(
        "deal_form.html",
        {
            "request": request,
            "role": role,
            "apartments": apartments,
            "clients": clients,
        },
    )


@app.post(
    "/deals/create",
    tags=["Deals"],
    summary="Створити угоду",
    description="Створює нову угоду оренди та змінює статус квартири на rented.",
)
def deal_create(
    request: Request,
    apartment_id: int = Form(...),
    client_id: int = Form(...),
    months: int = Form(...),
    db: Session = Depends(get_db),
):
    role = get_role(request)

    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    client = db.query(Client).filter(Client.id == client_id).first()

    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")
    if not client:
        raise HTTPException(status_code=404, detail="Клієнта не знайдено")
    if apartment.status != "available":
        raise HTTPException(status_code=400, detail="Квартира вже орендована")

    total_price = apartment.price * months

    deal = Deal(
        apartment_id=apartment_id,
        client_id=client_id,
        months=months,
        total_price=total_price,
    )
    apartment.status = "rented"

    db.add(deal)
    db.commit()

    return RedirectResponse(url=f"/deals?role={role}", status_code=303)


@app.get(
    "/api/apartments",
    tags=["Apartments API"],
    summary="Отримати всі квартири",
    description="Повертає список усіх квартир у форматі JSON.",
)
def api_get_apartments(db: Session = Depends(get_db)):
    apartments = db.query(Apartment).all()
    result = []
    for a in apartments:
        result.append(
            {
                "id": a.id,
                "title": a.title,
                "address": a.address,
                "rooms": a.rooms,
                "price": a.price,
                "status": a.status,
                "city": a.city.name,
                "landlord": a.landlord.full_name,
            }
        )
    return result


@app.get(
    "/api/apartments/{apartment_id}",
    tags=["Apartments API"],
    summary="Отримати квартиру за ID",
    description="Повертає одну квартиру у форматі JSON за її ідентифікатором.",
)
def api_get_apartment(apartment_id: int, db: Session = Depends(get_db)):
    a = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    return {
        "id": a.id,
        "title": a.title,
        "address": a.address,
        "rooms": a.rooms,
        "price": a.price,
        "status": a.status,
        "city_id": a.city_id,
        "landlord_id": a.landlord_id,
    }


@app.post(
    "/api/apartments",
    tags=["Apartments API"],
    summary="Створити квартиру через API",
    description="Створює нову квартиру та повертає її у JSON-форматі.",
)
def api_create_apartment(
    title: str = Form(...),
    address: str = Form(...),
    rooms: int = Form(...),
    price: int = Form(...),
    city_id: int = Form(...),
    landlord_id: int = Form(...),
    db: Session = Depends(get_db),
):
    apartment = Apartment(
        title=title,
        address=address,
        rooms=rooms,
        price=price,
        city_id=city_id,
        landlord_id=landlord_id,
        status="available",
    )
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    return apartment


@app.put(
    "/api/apartments/{apartment_id}",
    tags=["Apartments API"],
    summary="Оновити квартиру через API",
    description="Оновлює дані квартири за її ID та повертає оновлений JSON-об’єкт.",
)
def api_update_apartment(
    apartment_id: int,
    title: str = Form(...),
    address: str = Form(...),
    rooms: int = Form(...),
    price: int = Form(...),
    status: str = Form(...),
    city_id: int = Form(...),
    landlord_id: int = Form(...),
    db: Session = Depends(get_db),
):
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    apartment.title = title
    apartment.address = address
    apartment.rooms = rooms
    apartment.price = price
    apartment.status = status
    apartment.city_id = city_id
    apartment.landlord_id = landlord_id

    db.commit()
    db.refresh(apartment)
    return apartment


@app.delete(
    "/api/apartments/{apartment_id}",
    tags=["Apartments API"],
    summary="Видалити квартиру через API",
    description="Видаляє квартиру за її ID та повертає повідомлення про успішне видалення.",
)
def api_delete_apartment(apartment_id: int, db: Session = Depends(get_db)):
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    db.delete(apartment)
    db.commit()
    return {"message": "Квартиру видалено"}