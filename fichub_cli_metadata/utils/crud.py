# Copyright 2022 Arbaaz Laskar

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from tqdm import tqdm
import sys
from colorama import Fore
from loguru import logger
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from . import models
from .processing import process_extraMeta, get_ins_query, sql_to_json
from .logging import db_not_found_log


def insert_data(db: Session, item: dict, debug: bool):
    """ Execute insert query for the db
    """

    exists = db.query(models.Metadata).filter(
        models.Metadata.source == item['source']).first()

    if not exists:
        query = get_ins_query(item)
        db.add(query)
        if debug:
            logger.info("Adding metadata to the database.")
        tqdm.write(Fore.GREEN +
                   "Adding metadata to the database.")
        db.commit()
        return 0, 0
    else:
        if debug:
            logger.info(
                "Metadata already exists. Skipping. Use --force to force-update existing data.")
        tqdm.write(Fore.RED +
                   "Metadata already exists. Skipping. Use --force to force-update existing data.\n")
        return 1, 2


def update_data(db: Session, item: dict, debug: bool):
    """ Execute update query for the db
    """
    exists = db.query(models.Metadata).filter(
        models.Metadata.source == item['source']).first()
    if not exists:
        query = get_ins_query(item)
        db.add(query)
        if debug:
            logger.info("Adding metadata to the database.")
        tqdm.write(Fore.GREEN +
                   "Adding metadata to the database.")
    else:
        rated, language, genre, characters, reviews, favs, follows = process_extraMeta(
            item['extraMeta'])
        db.query(models.Metadata).filter(
            models.Metadata.source == item['source']). \
            update(
            {
                models.Metadata.fichub_id: item['id'],
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
                models.Metadata.words: item['words'],
                models.Metadata.fic_last_updated: item['updated'],
                models.Metadata.db_last_updated: datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z'),
                models.Metadata.source: item['source']
            }
        )
        if debug:
            logger.info(
                "Metadata already exists. Overwriting metadata to the database.")
        tqdm.write(Fore.GREEN +
                   "Metadata already exists. Overwriting metadata to the database.\n")

    db.commit()
    return 0, 0  # exit code


def dump_json(db: Session, input_db, json_file: str, debug: bool):
    """ Process the sqlite db and dump the metadata as json
    """
    if debug:
        logger.info("Getting all rows from database.")
    tqdm.write(Fore.GREEN + "Getting all rows from database.")
    try:
        all_rows = get_all_rows(db)
    except OperationalError as e:
        if debug:
            logger.info(Fore.RED + str(e))
        db_not_found_log(debug, input_db)
        sys.exit(1)

    sql_to_json(json_file, all_rows, debug)
    db.commit()


def get_all_rows(db: Session):
    return db.query(models.Metadata).all()


def add_fichub_id_column(db: Session, db_backup, debug: bool):
    """ To add a column AFTER an existing column
    """

    drop_TempFichubMetadata(db)
    col_exists = False
    try:
        col_exists = db.execute("SELECT fichub_id from fichub_metadata;")
        col_exists = True
    except OperationalError as e:
        if debug:
            logger.error(e)
        pass
    if not col_exists:
        tqdm.write(
            Fore.GREEN + "Database Schema changes detected! Migrating the database.")
        # backup the db before migrating the data
        db_backup("pre.migration")

        if debug:
            logger.info("Migration: adding fichub_id column")
        tqdm.write(Fore.GREEN + "Migration: adding fichub_id column")

        db.execute("ALTER TABLE fichub_metadata RENAME TO TempFichubMetadata;")
        db.execute("CREATE TABLE fichub_metadata(id INTEGER NOT NULL, fichub_id VARCHAR(255),title VARCHAR(255), author VARCHAR(255), chapters INTEGER, created VARCHAR(255), description VARCHAR(255), rated VARCHAR(255), language VARCHAR(255), genre VARCHAR(255), characters VARCHAR(255), reviews INTEGER, favs INTEGER, follows INTEGER, status VARCHAR(255), words INTEGER, last_updated VARCHAR(255), source VARCHAR(255), PRIMARY KEY(id))")
        db.execute("INSERT INTO fichub_metadata (id, title, author, chapters, created, description, rated, language, genre, characters, reviews, favs, follows, status, words, last_updated, source ) SELECT id, title, author, chapters, created, description, rated, language, genre, characters, reviews, favs, follows, status, words,last_updated, source FROM TempFichubMetadata;")
        db.execute("DROP TABLE TempFichubMetadata;")
        db.commit()


def add_db_last_updated_column(db: Session, db_backup, debug: bool):
    """ To add a column AFTER an existing column
    """

    drop_TempFichubMetadata(db)
    col_exists = False
    try:
        db.execute("SELECT db_last_updated from fichub_metadata;")
        col_exists = True
    except OperationalError as e:
        if debug:
            logger.error(e)
        pass
    if not col_exists:
        tqdm.write(
            Fore.GREEN + "Database Schema changes detected! Migrating the database.")
        # backup the db before migrating the data
        db_backup("pre.migration")

        if debug:
            logger.info("Migration: adding db_last_updated column")
        tqdm.write(Fore.GREEN + "Migration: adding db_last_updated column")

        db.execute("ALTER TABLE fichub_metadata RENAME TO TempFichubMetadata;")
        db.execute("CREATE TABLE fichub_metadata(id INTEGER NOT NULL, fichub_id VARCHAR(255), title VARCHAR(255), author VARCHAR(255), chapters INTEGER, created VARCHAR(255), description VARCHAR(255), rated VARCHAR(255), language VARCHAR(255), genre VARCHAR(255), characters VARCHAR(255), reviews INTEGER, favs INTEGER, follows INTEGER, status VARCHAR(255), words INTEGER, fic_last_updated VARCHAR(255), db_last_updated VARCHAR(255), source VARCHAR(255), PRIMARY KEY(id))")
        db.execute("INSERT INTO fichub_metadata (id, fichub_id, title, author, chapters, created, description, rated, language, genre, characters, reviews, favs, follows, status,  words, fic_last_updated, source ) SELECT id, fichub_id, title, author, chapters, created, description, rated, language, genre, characters, reviews, favs, follows, status, words, last_updated, source FROM TempFichubMetadata;")
        db.execute("DROP TABLE TempFichubMetadata;")
        db.commit()


def drop_TempFichubMetadata(db: Session):
    try:
        db.execute("DROP TABLE TempFichubMetadata;")
    except OperationalError:
        pass
