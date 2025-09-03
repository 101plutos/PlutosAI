from sqlalchemy import Column, String, Enum, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Index

from shared.domain.client import ClientType, ClientStatus

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'

    id = Column(String, primary_key=True)
    type = Column(Enum(ClientType), nullable=False)
    status = Column(Enum(ClientStatus), nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_clients_status', 'status'),
        Index('ix_clients_created_at', 'created_at'),
    )