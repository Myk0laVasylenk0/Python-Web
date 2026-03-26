from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from pymongo import AsyncMongoClient

from models import City, Landlord, Client, Apartment, Deal


MONGO_URL = "mongodb://127.0.0.1:27017"
MONGO_DB_NAME = "apartment_rental_1"

client: AsyncMongoClient | None = None


async def init_db() -> None:
    global client

    client = AsyncMongoClient(MONGO_URL)
    database = client[MONGO_DB_NAME]

    await init_beanie(
        database=database,
        document_models=[City, Landlord, Client, Apartment, Deal],
    )


async def close_db() -> None:
    global client

    if client is not None:
        await client.close()
        client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()
