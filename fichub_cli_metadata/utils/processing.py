import typer
from colorama import Fore
from loguru import logger
import json
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from . import models


def init_database(db):

    engine = create_engine("sqlite:///"+db)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine, SessionLocal


def get_db(SessionLocal):
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def process_extraMeta(extraMeta: str):
    extraMeta = extraMeta.split('-')

    for x in extraMeta:
        if x.strip().startswith("Rated:"):
            rated = x.replace('Rated:', '').strip()
            break
        else:
            rated = None

    for x in extraMeta:
        if x.strip().startswith("Language:"):
            language = x.replace('Language:', '').strip()
            break
        else:
            language = None

    for x in extraMeta:
        if x.strip().startswith("Genre:"):
            genre = x.replace('Genre:', '').strip()
            break
        else:
            genre = None

    for x in extraMeta:
        if x.strip().startswith("Characters:"):
            characters = x.replace('Characters:', '').strip()
            break
        else:
            characters = None

    for x in extraMeta:
        if x.strip().startswith("Reviews:"):
            reviews = x.replace('Reviews:', '').strip()
            break
        else:
            reviews = None

    for x in extraMeta:
        if x.strip().startswith("Favs:"):
            favs = x.replace('Favs:', '').strip()
            break
        else:
            favs = None

    for x in extraMeta:
        if x.strip().startswith("Follows:"):
            follows = x.replace('Follows:', '').strip()
            break
        else:
            follows = None

    return rated, language, genre, characters, reviews, favs, follows


def get_ins_query(item: dict):
    rated, language, genre, characters, reviews, favs, follows = process_extraMeta(
        item['extraMeta'])

    query = models.Metadata(
        title=item['title'],
        author=item['author'],
        chapters=item['chapters'],
        created=item['created'],
        description=item['description'],
        rated=rated,
        language=language,
        genre=genre,
        characters=characters,
        reviews=reviews,
        favs=favs,
        follows=follows,
        status=item['status'],
        last_updated=item['updated'],
        words=item['words'],
        source=item['source']

    )
    return query


def sql_to_json(json_file: str, query_output, debug):
    """ Converts output from a SQLAlchemy query to a .json file.
    """
    meta_list = []
    for row in query_output:
        row_dict = object_as_dict(row)
        if debug:
            logger.info(f"Processing {row_dict['source']}")
        typer.echo(Fore.BLUE+f"Processing {row_dict['source']}")
        meta_list.append(json.dumps(row_dict, indent=4))

    meta_data = "{\"meta\": ["
    for i in meta_list:
        meta_data += str(i)+","
    meta_data += "]}"

    if meta_list:
        with open(json_file, 'w') as outfile:
            if debug:
                logger.info(f"Saving {json_file}")
            typer.echo(Fore.GREEN+f"Saving {json_file}")
            outfile.write(meta_data)


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}
