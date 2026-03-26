from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    apartments = relationship("Apartment", back_populates="city", cascade="all, delete")


class Landlord(Base):
    __tablename__ = "landlords"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)

    apartments = relationship("Apartment", back_populates="landlord", cascade="all, delete")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)

    deals = relationship("Deal", back_populates="client", cascade="all, delete")


class Apartment(Base):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    address = Column(String, nullable=False)
    rooms = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String, default="available")

    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    landlord_id = Column(Integer, ForeignKey("landlords.id"), nullable=False)

    city = relationship("City", back_populates="apartments")
    landlord = relationship("Landlord", back_populates="apartments")
    deals = relationship("Deal", back_populates="apartment", cascade="all, delete")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    months = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)

    apartment = relationship("Apartment", back_populates="deals")
    client = relationship("Client", back_populates="deals")
