from tqdm import tqdm
import sys
from colorama import Fore
from loguru import logger
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from . import models
from .processing import process_extraMeta, get_ins_query, sql_to_json


def insert_data(db: Session, item: dict, debug: bool):
    exists = db.query(models.Metadata).filter(
        models.Metadata.source == item['source']).first()
    if not exists:
        query = get_ins_query(item)
        db.add(query)
        if debug:
            logger.info("Adding metadata.")
        tqdm.write(Fore.GREEN +
                   "Adding metadata.")
    else:
        if debug:
            logger.info(
                "Metadata already exists. Skipping. Use --update-db to update existing data.")
        tqdm.write(Fore.RED +
                   "Metadata already exists. Skipping. Use --update-db to update existing data.\n")

    db.commit()


def update_data(db: Session, item: dict, debug: bool):

    exists = db.query(models.Metadata).filter(
        models.Metadata.source == item['source']).first()
    if not exists:
        query = get_ins_query(item)
        db.add(query)
        if debug:
            logger.info("Adding metadata.")
        tqdm.write(Fore.GREEN +
                   "Adding metadata.")
    else:
        rated, language, genre, characters, reviews, favs, follows = process_extraMeta(
            item['extraMeta'])
        db.query(models.Metadata).filter(
            models.Metadata.source == item['source']). \
            update(
            {
                models.Metadata.title: item['title'],
                models.Metadata.author: item['author'],
                models.Metadata.chapters: item['chapters'],
                models.Metadata.created: item['created'],
                models.Metadata.description: item['description'],
                models.Metadata.rated: rated,
                models.Metadata.language: language,
                models.Metadata.genre: genre,
                models.Metadata.characters: characters,
                models.Metadata.reviews: reviews,
                models.Metadata.favs: favs,
                models.Metadata.follows: follows,
                models.Metadata.status: item['status'],
                models.Metadata.last_updated: item['updated'],
                models.Metadata.words: item['words'],
                models.Metadata.source: item['source']
            }
        )
        if debug:
            logger.info("Metadata already exists. Updating metadata.")
        tqdm.write(Fore.GREEN +
                   "Metadata already exists. Updating metadata.\n")

    db.commit()


def dump_json(db: Session, input_db, json_file: str, debug: bool):

    if debug:
        logger.info("Getting all rows from database.")
    tqdm.write(Fore.GREEN + "Getting all rows from database.")
    try:
        all_rows = get_all_rows(db)
    except OperationalError:
        tqdm.write(
            Fore.RED + f"Unable to open database file: {input_db}\nPlease recheck the filename!")
        if debug:
            logger.error(
                f"Unable to open database file: {input_db}\nPlease recheck the filename!")
        sys.exit()

    sql_to_json(json_file, all_rows, debug)
    db.commit()


def get_all_rows(db: Session):
    return db.query(models.Metadata).all()
