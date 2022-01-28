from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Metadata(Base):
    __tablename__ = "fichub_metadata"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)
    chapters = Column(Integer)
    created = Column(String)
    description = Column(String)
    rated = Column(String)
    language = Column(String)
    genre = Column(String)
    characters = Column(String)
    reviews = Column(Integer)
    favs = Column(Integer)
    follows = Column(Integer)
    status = Column(String)
    last_updated = Column(String)
    words = Column(Integer)
    source = Column(String)
