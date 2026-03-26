from pydantic import BaseModel


class ApartmentCreate(BaseModel):
    title: str
    address: str
    rooms: int
    price: int
    city_id: int
    landlord_id: int


class ApartmentUpdate(ApartmentCreate):
    status: str
