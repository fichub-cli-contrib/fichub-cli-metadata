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
from colorama import Fore, Style
from loguru import logger
import json
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from . import models


def init_database(db):
    """ Initialize the sqlite database
    """

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
    """ Process the extraMetadata string and return
        fields like language, genre etc
    """
    try:
        extraMeta = extraMeta.split('-')
    except AttributeError:
        tqdm.write(Fore.RED +
                   "'extraMetadata' key not found in the API response. Adding Null for missing fields.")
        extraMeta = ['']
        pass

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
    """ Return the insert query for the db model
    """

    rated, language, genre, characters, reviews, favs, follows = process_extraMeta(
        item['extraMeta'])

    query = models.Metadata(
        fichub_id=item['id'],
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
        words=item['words'],
        fic_last_updated=item['updated'],
        db_last_updated=datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z'),
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
        tqdm.write(Fore.BLUE+f"Processing {row_dict['source']}")
        meta_list.append(row_dict)

    if meta_list:
        with open(json_file, 'w') as outfile:
            if debug:
                logger.info(f"Saving {json_file}")
            tqdm.write(Fore.GREEN+f"Saving {json_file}")
            json.dump(meta_list, outfile)


def object_as_dict(obj):
    """
    Convert a sqlalchemy object into a dictionary
    """
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def prompt_user_contact():
    tqdm.write(f"""
{Fore.BLUE}Please enter a contact email ID which will be included in the user-agent so that
AO3 can contact you to resolve any issues. AO3 staff advises that we should include the 
contact email if we are going to send a lot of requests in a short period of time. 
If you dont want to include any contact info, you can skip it by leaving it blank and pressing enter.{Style.RESET_ALL}""")
    return input("Contact: ")
