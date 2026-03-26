from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import lifespan
from models import City, Landlord, Client, Apartment, Deal


app = FastAPI(
    title="Система оренди квартир API",
    summary="Навчальний REST API для предметної області 'Оренда квартир'",
    description="""
API для вебзастосунку з серверною генерацією HTML та роботою з базою даних MongoDB.

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
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_role(request: Request) -> str:
    role = request.query_params.get("role", "user")
    if role not in ["admin", "user"]:
        return "user"
    return role


def normalize_doc(document):
    if document is None:
        return None

    data = document.model_dump()

    # Для шаблонів і JSON зручно віддавати pg_id як id
    if "pg_id" in data:
        data["id"] = data["pg_id"]

    # Прибираємо службовий Mongo _id, якщо він є
    data.pop("_id", None)

    return data


def normalize_docs(documents):
    return [normalize_doc(doc) for doc in documents]


async def get_city_by_id(city_id: int):
    return await City.find_one(City.pg_id == city_id)


async def get_landlord_by_id(landlord_id: int):
    return await Landlord.find_one(Landlord.pg_id == landlord_id)


async def get_client_by_id(client_id: int):
    return await Client.find_one(Client.pg_id == client_id)


async def get_apartment_by_id(apartment_id: int):
    return await Apartment.find_one(Apartment.pg_id == apartment_id)


async def get_next_id(model):
    last_item = await model.find_all().sort("-pg_id").first_or_none()
    if last_item is None:
        return 1
    return last_item.pg_id + 1


async def seed_data():
    if await City.count() == 0:
        await City(pg_id=1, name="Київ").insert()
        await City(pg_id=2, name="Львів").insert()

    if await Landlord.count() == 0:
        await Landlord(pg_id=1, full_name="Іван Петренко", phone="+380501111111").insert()
        await Landlord(pg_id=2, full_name="Олена Коваль", phone="+380502222222").insert()

    if await Client.count() == 0:
        await Client(pg_id=1, full_name="Марія Іваненко", phone="+380503333333").insert()
        await Client(pg_id=2, full_name="Олексій Бондар", phone="+380504444444").insert()

    if await Apartment.count() == 0:
        await Apartment(
            pg_id=1,
            title="1-кімнатна квартира біля метро",
            address="вул. Хрещатик, 10",
            rooms=1,
            price=12000,
            status="available",
            city_id=1,
            landlord_id=1,
        ).insert()

        await Apartment(
            pg_id=2,
            title="2-кімнатна квартира в центрі",
            address="просп. Свободи, 15",
            rooms=2,
            price=18000,
            status="available",
            city_id=2,
            landlord_id=2,
        ).insert()


@app.on_event("startup")
async def on_startup():
    await seed_data()


@app.get(
    "/",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Головна сторінка",
    description="Повертає головну HTML-сторінку системи оренди квартир.",
)
async def home(request: Request):
    role = get_role(request)
    apartments_raw = await Apartment.find_all().to_list()

    apartments = []
    for apartment in apartments_raw:
        city = await get_city_by_id(apartment.city_id)
        landlord = await get_landlord_by_id(apartment.landlord_id)

        apartments.append(
            {
                "id": apartment.pg_id,
                "pg_id": apartment.pg_id,
                "title": apartment.title,
                "address": apartment.address,
                "rooms": apartment.rooms,
                "price": apartment.price,
                "status": apartment.status,
                "city_id": apartment.city_id,
                "landlord_id": apartment.landlord_id,
                "city": normalize_doc(city) if city else None,
                "landlord": normalize_doc(landlord) if landlord else None,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
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
async def apartment_list(request: Request):
    role = get_role(request)
    apartments_raw = await Apartment.find_all().to_list()

    apartments = []
    for apartment in apartments_raw:
        city = await get_city_by_id(apartment.city_id)
        landlord = await get_landlord_by_id(apartment.landlord_id)

        apartments.append(
            {
                "id": apartment.pg_id,
                "pg_id": apartment.pg_id,
                "title": apartment.title,
                "address": apartment.address,
                "rooms": apartment.rooms,
                "price": apartment.price,
                "status": apartment.status,
                "city_id": apartment.city_id,
                "landlord_id": apartment.landlord_id,
                "city": normalize_doc(city) if city else None,
                "landlord": normalize_doc(landlord) if landlord else None,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="apartments.html",
        context={
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
async def apartment_create_page(request: Request):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може створювати квартири")

    cities = normalize_docs(await City.find_all().to_list())
    landlords = normalize_docs(await Landlord.find_all().to_list())

    return templates.TemplateResponse(
        request=request,
        name="apartment_form.html",
        context={
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
async def apartment_create(
    request: Request,
    title: str = Form(...),
    address: str = Form(...),
    rooms: int = Form(...),
    price: int = Form(...),
    city_id: int = Form(...),
    landlord_id: int = Form(...),
):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може створювати квартири")

    city = await get_city_by_id(city_id)
    landlord = await get_landlord_by_id(landlord_id)

    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдено")
    if not landlord:
        raise HTTPException(status_code=404, detail="Орендодавця не знайдено")

    apartment = Apartment(
        pg_id=await get_next_id(Apartment),
        title=title,
        address=address,
        rooms=rooms,
        price=price,
        city_id=city.pg_id,
        landlord_id=landlord.pg_id,
        status="available",
    )
    await apartment.insert()

    return RedirectResponse(url=f"/apartments?role={role}", status_code=303)


@app.get(
    "/apartments/{apartment_id}/edit",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Сторінка редагування квартири",
    description="Повертає HTML-форму для редагування квартири за її ID.",
)
async def apartment_edit_page(apartment_id: int, request: Request):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може редагувати квартири")

    apartment = await get_apartment_by_id(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    cities = normalize_docs(await City.find_all().to_list())
    landlords = normalize_docs(await Landlord.find_all().to_list())

    return templates.TemplateResponse(
        request=request,
        name="apartment_form.html",
        context={
            "request": request,
            "role": role,
            "cities": cities,
            "landlords": landlords,
            "apartment": normalize_doc(apartment),
        },
    )


@app.post(
    "/apartments/{apartment_id}/edit",
    tags=["Pages"],
    summary="Оновити квартиру",
    description="Обробляє HTML-форму та оновлює квартиру за її ID.",
)
async def apartment_edit(
    apartment_id: int,
    request: Request,
    title: str = Form(...),
    address: str = Form(...),
    rooms: int = Form(...),
    price: int = Form(...),
    status: str = Form(...),
    city_id: int = Form(...),
    landlord_id: int = Form(...),
):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може редагувати квартири")

    apartment = await get_apartment_by_id(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    city = await get_city_by_id(city_id)
    landlord = await get_landlord_by_id(landlord_id)

    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдено")
    if not landlord:
        raise HTTPException(status_code=404, detail="Орендодавця не знайдено")

    apartment.title = title
    apartment.address = address
    apartment.rooms = rooms
    apartment.price = price
    apartment.status = status
    apartment.city_id = city.pg_id
    apartment.landlord_id = landlord.pg_id

    await apartment.save()

    return RedirectResponse(url=f"/apartments?role={role}", status_code=303)


@app.post(
    "/apartments/{apartment_id}/delete",
    tags=["Pages"],
    summary="Видалити квартиру",
    description="Видаляє квартиру за її ID через HTML-інтерфейс.",
)
async def apartment_delete(apartment_id: int, request: Request):
    role = get_role(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Лише адміністратор може видаляти квартири")

    apartment = await get_apartment_by_id(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    await apartment.delete()

    return RedirectResponse(url=f"/apartments?role={role}", status_code=303)


@app.get(
    "/cities",
    response_class=HTMLResponse,
    tags=["Reference"],
    summary="Список міст",
    description="Повертає HTML-сторінку зі списком міст.",
)
async def city_list(request: Request):
    role = get_role(request)
    cities = normalize_docs(await City.find_all().to_list())

    return templates.TemplateResponse(
        request=request,
        name="cities.html",
        context={
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
async def landlord_list(request: Request):
    role = get_role(request)
    landlords = normalize_docs(await Landlord.find_all().to_list())

    return templates.TemplateResponse(
        request=request,
        name="landlords.html",
        context={
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
async def client_list(request: Request):
    role = get_role(request)
    clients = normalize_docs(await Client.find_all().to_list())

    return templates.TemplateResponse(
        request=request,
        name="clients.html",
        context={
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
async def deal_list(request: Request):
    role = get_role(request)
    deals_raw = await Deal.find_all().to_list()

    deals = []
    for deal in deals_raw:
        apartment = await get_apartment_by_id(deal.apartment_id)
        client = await get_client_by_id(deal.client_id)

        deals.append(
            {
                "id": deal.pg_id,
                "pg_id": deal.pg_id,
                "months": deal.months,
                "total_price": deal.total_price,
                "apartment_id": deal.apartment_id,
                "client_id": deal.client_id,
                "apartment": normalize_doc(apartment) if apartment else None,
                "client": normalize_doc(client) if client else None,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="deals.html",
        context={
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
async def deal_create_page(request: Request):
    role = get_role(request)
    apartments = normalize_docs(await Apartment.find(Apartment.status == "available").to_list())
    clients = normalize_docs(await Client.find_all().to_list())

    return templates.TemplateResponse(
        request=request,
        name="deal_form.html",
        context={
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
async def deal_create(
    request: Request,
    apartment_id: int = Form(...),
    client_id: int = Form(...),
    months: int = Form(...),
):
    role = get_role(request)

    apartment = await get_apartment_by_id(apartment_id)
    client = await get_client_by_id(client_id)

    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")
    if not client:
        raise HTTPException(status_code=404, detail="Клієнта не знайдено")
    if apartment.status != "available":
        raise HTTPException(status_code=400, detail="Квартира вже орендована")

    total_price = apartment.price * months

    deal = Deal(
        pg_id=await get_next_id(Deal),
        apartment_id=apartment.pg_id,
        client_id=client.pg_id,
        months=months,
        total_price=total_price,
    )
    await deal.insert()

    apartment.status = "rented"
    await apartment.save()

    return RedirectResponse(url=f"/deals?role={role}", status_code=303)


@app.get(
    "/api/apartments",
    tags=["Apartments API"],
    summary="Отримати всі квартири",
    description="Повертає список усіх квартир у форматі JSON.",
)
async def api_get_apartments():
    apartments = await Apartment.find_all().to_list()
    result = []

    for apartment in apartments:
        city = await get_city_by_id(apartment.city_id)
        landlord = await get_landlord_by_id(apartment.landlord_id)

        result.append(
            {
                "id": apartment.pg_id,
                "title": apartment.title,
                "address": apartment.address,
                "rooms": apartment.rooms,
                "price": apartment.price,
                "status": apartment.status,
                "city": city.name if city else None,
                "landlord": landlord.full_name if landlord else None,
            }
        )

    return result


@app.get(
    "/api/apartments/{apartment_id}",
    tags=["Apartments API"],
    summary="Отримати квартиру за ID",
    description="Повертає одну квартиру у форматі JSON за її ідентифікатором.",
)
async def api_get_apartment(apartment_id: int):
    apartment = await get_apartment_by_id(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    return {
        "id": apartment.pg_id,
        "title": apartment.title,
        "address": apartment.address,
        "rooms": apartment.rooms,
        "price": apartment.price,
        "status": apartment.status,
        "city_id": apartment.city_id,
        "landlord_id": apartment.landlord_id,
    }


@app.post(
    "/api/apartments",
    tags=["Apartments API"],
    summary="Створити квартиру через API",
    description="Створює нову квартиру та повертає її у JSON-форматі.",
)
async def api_create_apartment(
    title: str = Form(...),
    address: str = Form(...),
    rooms: int = Form(...),
    price: int = Form(...),
    city_id: int = Form(...),
    landlord_id: int = Form(...),
):
    city = await get_city_by_id(city_id)
    landlord = await get_landlord_by_id(landlord_id)

    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдено")
    if not landlord:
        raise HTTPException(status_code=404, detail="Орендодавця не знайдено")

    apartment = Apartment(
        pg_id=await get_next_id(Apartment),
        title=title,
        address=address,
        rooms=rooms,
        price=price,
        city_id=city.pg_id,
        landlord_id=landlord.pg_id,
        status="available",
    )
    await apartment.insert()

    return normalize_doc(apartment)


@app.put(
    "/api/apartments/{apartment_id}",
    tags=["Apartments API"],
    summary="Оновити квартиру через API",
    description="Оновлює дані квартири за її ID та повертає оновлений JSON-об’єкт.",
)
async def api_update_apartment(
    apartment_id: int,
    title: str = Form(...),
    address: str = Form(...),
    rooms: int = Form(...),
    price: int = Form(...),
    status: str = Form(...),
    city_id: int = Form(...),
    landlord_id: int = Form(...),
):
    apartment = await get_apartment_by_id(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    city = await get_city_by_id(city_id)
    landlord = await get_landlord_by_id(landlord_id)

    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдено")
    if not landlord:
        raise HTTPException(status_code=404, detail="Орендодавця не знайдено")

    apartment.title = title
    apartment.address = address
    apartment.rooms = rooms
    apartment.price = price
    apartment.status = status
    apartment.city_id = city.pg_id
    apartment.landlord_id = landlord.pg_id

    await apartment.save()

    return normalize_doc(apartment)


@app.delete(
    "/api/apartments/{apartment_id}",
    tags=["Apartments API"],
    summary="Видалити квартиру через API",
    description="Видаляє квартиру за її ID та повертає повідомлення про успішне видалення.",
)
async def api_delete_apartment(apartment_id: int):
    apartment = await get_apartment_by_id(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Квартиру не знайдено")

    await apartment.delete()
    return {"message": "Квартиру видалено"}