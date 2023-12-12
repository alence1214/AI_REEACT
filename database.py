from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://honey:honey@127.0.0.1:3306/reeact"
# SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://honey:honey@127.0.0.1:3306/reeact"
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:password@127.0.0.1:3306/reeact_test"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

metadata = MetaData(bind=engine)
metadata.reflect()

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
