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
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from platformdirs import PlatformDirs

from . import models
app_dirs = PlatformDirs("fichub_cli", "fichub")


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


def get_ins_query(item: dict):
    """ Return the insert query for the db model
    """
    try:
        with open(os.path.join(app_dirs.user_data_dir, "config.json"), 'r') as f:
            config = json.load(f)
    except FileNotFoundError as err:
        tqdm.write(str(err))
        tqdm.write(
            Fore.GREEN + "Run `fichub_cli --config-init` to initialize the CLI config")
        exit(1)

    query = models.Metadata(
        fichub_id=item['id'],
        fic_id = (item['rawExtendedMeta']['id'] if 'id' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        title=item['title'],
        author=item['author'],
        author_id=item['authorLocalId'],
        author_url=item['authorUrl'],
        chapters=item['chapters'],
        created=item['created'],
        description=item['description'],
        rated=(item['rawExtendedMeta']['rated'] if 'rated' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        language=(item['rawExtendedMeta']['language'] if 'language' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        genre=(item['rawExtendedMeta']['genres'] if 'genres' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        characters=(item['rawExtendedMeta']['characters'] if 'characters' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        reviews=(item['rawExtendedMeta']['reviews'] if 'reviews' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        favorites=(item['rawExtendedMeta']['favorites'] if 'favorites' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        follows=(item['rawExtendedMeta']['follows'] if 'follows' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        status=item['status'],
        words=item['words'],
        fandom = (item['rawExtendedMeta']['raw_fandom'] if 'raw_fandom' in item['rawExtendedMeta'] else None) if item['rawExtendedMeta'] != None else None,
        fic_last_updated=datetime.strptime(item['updated'], r'%Y-%m-%dT%H:%M:%S').strftime(
            config['fic_up_time_format']),
        db_last_updated=datetime.now().astimezone().strftime(
            config['db_up_time_format']),
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
