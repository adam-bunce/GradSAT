from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, Integer


class Base(DeclarativeBase):
    pass


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = Column(Integer, primary_key=True)
    data: Mapped[JSONB] = Column(JSONB)
