import typer
from colorama import Fore
from loguru import logger

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
        typer.echo(Fore.GREEN +
                   "Adding metadata.")
    else:
        if debug:
            logger.info(
                "Metadata already exists. Skipping. Use --update-db to update existing data.")
        typer.echo(Fore.RED +
                   "Metadata already exists. Skipping. Use --update-db to update existing data.")

    db.commit()


def update_data(db: Session, item: dict, debug: bool):

    exists = db.query(models.Metadata).filter(
        models.Metadata.source == item['source']).first()
    if not exists:
        query = get_ins_query(item)
        db.add(query)
        if debug:
            logger.info("Adding metadata.")
        typer.echo(Fore.GREEN +
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
        typer.echo(Fore.GREEN +
                   "Metadata already exists. Updating metadata.")

    db.commit()


def dump_json(db: Session, json_file: str, debug: bool):
    if debug:
        logger.info("Getting all rows from database.")
    typer.echo(Fore.GREEN + "Getting all rows from database.")
    all_rows = db.query(models.Metadata).all()
    sql_to_json(json_file, all_rows, debug)
    db.commit()
