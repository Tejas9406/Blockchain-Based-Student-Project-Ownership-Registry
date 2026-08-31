from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base class for all ORM models.
    Domain models will inherit from this Base in future phases.
    """
    pass
