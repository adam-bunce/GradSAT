import os
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from scout_platform.db.schema import Base


def create_url():
    env_path = Path(__file__).parent / "db.env"
    load_dotenv(env_path)

    db_host = os.environ["db_host"] or "localhost"
    db_user = os.environ["db_user"] or "postgres"
    db_name = os.environ["db_name"] or "postgres"
    db_password = os.environ["db_pass"] or "123"
    db_port = os.environ["db_port"] or 5432

    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return database_url


@lru_cache
def get_session_factory(url: str) -> sessionmaker:
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            print("created table", table_name)
            table.create(engine)

    return sessionmaker(bind=engine)


@contextmanager
def get_db(url: str):
    factory = get_session_factory(url)
    session = factory()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    url = create_url()
    print(url)
    with get_db(url) as db:
        print(db.info)

