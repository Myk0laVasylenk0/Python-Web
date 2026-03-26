from beanie import Document
from pydantic import Field


class City(Document):
    pg_id: int
    name: str = Field(..., min_length=1)

    class Settings:
        name = "cities"


class Landlord(Document):
    pg_id: int
    full_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)

    class Settings:
        name = "landlords"


class Client(Document):
    pg_id: int
    full_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)

    class Settings:
        name = "clients"


class Apartment(Document):
    pg_id: int
    title: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    rooms: int = Field(..., ge=1)
    price: int = Field(..., ge=0)
    status: str = Field(default="available")
    city_id: int
    landlord_id: int

    class Settings:
        name = "apartments"


class Deal(Document):
    pg_id: int
    apartment_id: int
    client_id: int
    months: int = Field(..., ge=1)
    total_price: int = Field(..., ge=0)

    class Settings:
        name = "deals"