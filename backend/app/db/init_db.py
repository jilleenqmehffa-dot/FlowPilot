"""Create the V1 schema explicitly; this is not a schema migration tool."""

from backend.app import models  # noqa: F401 -- register every table on Base.metadata
from backend.app.db.base import Base
from backend.app.db.database import get_engine


def main() -> None:
    engine = get_engine()
    try:
        with engine.begin() as connection:
            Base.metadata.create_all(connection)
        print("CRM V1 database tables created (existing tables left unchanged).")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
