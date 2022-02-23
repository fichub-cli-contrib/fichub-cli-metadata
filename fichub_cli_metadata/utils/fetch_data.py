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

import os
import sys
import shutil
from datetime import datetime
import sqlalchemy
from tqdm import tqdm
import typer
from colorama import Fore, Style
from loguru import logger
from rich.console import Console
import re
import requests
from bs4 import BeautifulSoup

from sqlalchemy.orm import Session

from .fichub import FicHub
from .logging import meta_fetched_log, db_not_found_log
from . import models, crud
from .processing import init_database, get_db, object_as_dict

from fichub_cli.utils.logging import download_processing_log
from fichub_cli.utils.processing import check_url, save_data, check_output_log

bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt}, {rate_fmt}{postfix}, ETA: {remaining}"
console = Console()


class FetchData:
    def __init__(self, out_dir="", input_db="", update_db=False, format_type=None,
                 export_db=False, debug=False, automated=False, force=False):
        self.out_dir = out_dir
        self.format_type = format_type
        self.input_db = input_db
        self.update_db = update_db
        self.export_db = export_db
        self.force = force
        self.debug = debug
        self.automated = automated
        self.exit_status = 0

    def save_metadata(self, input: str):
        """ Store the metadata in the sqlite database
        """
        db_name = "fichub_metadata"
        supported_url = None

        # check if the input is a file
        if os.path.isfile(input):
            if self.debug:
                logger.info(f"Input file: {input}")
            # get the tail
            _, file_name = os.path.split(input)
            db_name = os.path.splitext(file_name)[0]
            with open(input, "r") as f:
                urls_input = f.read().splitlines()

        else:
            if self.debug:
                logger.info("Input is an URL")
            urls_input = [input]

        try:
            urls = check_output_log(urls_input, self.debug)

        # if output.log doesnt exist, when run 1st time
        except FileNotFoundError:
            urls = urls_input

        if not self.input_db:  # create db if no existing db is given
            timestamp = datetime.now().strftime("%Y-%m-%d T%H%M%S")
            self.db_file = os.path.join(
                self.out_dir, db_name) + f" - {timestamp}.sqlite"
        else:
            self.db_file = self.input_db

        self.engine, self.SessionLocal = init_database(self.db_file)
        self.db: Session = next(get_db(self.SessionLocal))

        try:
            # backup the db before changing the data
            self.db_backup()
        except FileNotFoundError:
            # when run 1st time, no db exists
            pass

        if urls:
            with tqdm(total=len(urls), ascii=False,
                      unit="url", bar_format=bar_format) as pbar:

                for url in urls:
                    download_processing_log(self.debug, url)
                    supported_url, self.exit_status = check_url(
                        url, self.debug, self.exit_status)

                    if supported_url:
                        # check if url exists in db
                        if self.input_db:
                            exists = self.db.query(models.Metadata).filter(
                                models.Metadata.source == url).first()
                        else:
                            exists = None

                        if not exists or self.force:
                            fic = FicHub(self.debug, self.automated,
                                         self.exit_status)
                            fic.get_fic_metadata(url, self.format_type)

                            try:
                                # if --download-ebook flag used
                                if self.format_type is not None:
                                    self.exit_status = save_data(
                                        self.out_dir, fic.file_name,
                                        fic.download_url, self.debug, self.force,
                                        fic.cache_hash, self.exit_status,
                                        self.automated)

                                # save the data to db
                                if fic.fic_metadata:
                                    meta_fetched_log(self.debug, url)
                                    self.save_to_db(fic.fic_metadata)

                                    with open("output.log", "a") as file:
                                        file.write(f"{url}\n")

                                    # update the exit status
                                    self.exit_status = fic.exit_status
                                else:
                                    self.exit_status = 1
                                    supported_url = None

                                pbar.update(1)

                            # if fic doesnt exist or the data is not fetched by the API yet
                            except AttributeError:
                                with open("err.log", "a") as file:
                                    file.write(url.strip()+"\n")
                                self.exit_status = 1
                                pbar.update(1)
                                pass  # skip the unsupported url
                        else:
                            self.exit_status = 1
                            supported_url = None
                            pbar.update(1)
                            if self.debug:
                                logger.info(
                                    "Metadata already exists. Skipping. Use --force to force-update existing data.")
                            tqdm.write(Fore.RED +
                                       "Metadata already exists. Skipping. Use --force to force-update existing data.\n")

                if self.exit_status == 0:
                    tqdm.write(Fore.GREEN +
                               "\nMetadata saved as " + Fore.BLUE +
                               f"{os.path.abspath(self.db_file)}"+Style.RESET_ALL +
                               Style.RESET_ALL)
        else:
            typer.echo(Fore.RED +
                       "No new urls found! If output.log exists, please clear it.")

    def save_to_db(self, item):
        """ Create the dn and execute insert or update crud
            repectively
        """
        try:
            models.Base.metadata.create_all(bind=self.engine)
        except sqlalchemy.exc.OperationalError:
            db_not_found_log(self.debug, self.db_file)
            sys.exit()

        # if force=True, dont insert, skip to else & update instead
        if not self.update_db and not self.force:
            self.exit_status = crud.insert_data(self.db, item, self.debug)

        elif self.update_db and not self.input_db == "" or self.force:
            self.exit_status = crud.update_data(self.db, item, self.debug)

    def update_metadata(self):
        """ Update the metadata found in the sqlite database
        """
        if os.path.isfile(self.input_db):
            self.db_file = self.input_db
            self.engine, self.SessionLocal = init_database(self.db_file)
        else:
            db_not_found_log(self.debug, self.input_db)
            sys.exit()

        self.db: Session = next(get_db(self.SessionLocal))
        if self.debug:
            logger.info("Getting all rows from database.")
        tqdm.write(Fore.GREEN + "Getting all rows from database.")
        try:
            all_rows = crud.get_all_rows(self.db)
        except sqlalchemy.exc.OperationalError:
            db_not_found_log(self.debug, self.db_file)
            sys.exit()

        # get the urls from the db
        urls_input = []
        for row in all_rows:
            row_dict = object_as_dict(row)
            urls_input.append(row_dict['source'])

        try:
            urls = check_output_log(urls_input, self.debug)

        # if output.log doesnt exist, when run 1st time
        except FileNotFoundError:
            urls = urls_input

        # backup the db before changing the data
        self.db_backup()
        with tqdm(total=len(urls), ascii=False,
                  unit="url", bar_format=bar_format) as pbar:

            for url in urls:
                fic = FicHub(self.debug, self.automated,
                             self.exit_status)
                fic.get_fic_metadata(url, self.format_type)

                try:
                    # if --download-ebook flag used
                    if self.format_type is not None:
                        self.exit_status = save_data(
                            self.out_dir, fic.file_name,
                            fic.download_url, self.debug, self.force,
                            fic.cache_hash, self.exit_status,
                            self.automated)

                    # update the metadata
                    if fic.fic_metadata:
                        meta_fetched_log(self.debug, url)
                        self.exit_status = crud.update_data(
                            self.db, fic.fic_metadata, self.debug)

                        with open("output.log", "a") as file:
                            file.write(f"{url}\n")
                    else:
                        self.exit_status = 1

                    pbar.update(1)

                # if fic doesnt exist or the data is not fetched by the API yet
                except AttributeError:
                    with open("err.log", "a") as file:
                        file.write(url+"\n")
                    self.exit_status = 1
                    pbar.update(1)
                    pass  # skip the unsupported url

    def export_db_as_json(self):
        _, file_name = os.path.split(self.input_db)
        self.db_name = os.path.splitext(file_name)[0]
        self.json_file = os.path.join(self.out_dir, self.db_name)+".json"

        if os.path.isfile(self.input_db):
            self.engine, self.SessionLocal = init_database(self.input_db)
        else:
            db_not_found_log(self.debug, self.input_db)
            sys.exit()

        if self.input_db:
            self.db: Session = next(get_db(self.SessionLocal))
            crud.dump_json(self.db, self.input_db, self.json_file, self.debug)
        else:
            tqdm.write(Fore.RED +
                       "SQLite db is not found. Use an existing sqlite db using: --input-db ")

    def db_backup(self):
        """ Creates a backup db in the same directory as the sqlite db
        """
        backup_out_dir, file_name = os.path.split(self.db_file)
        db_name = os.path.splitext(file_name)[0]
        shutil.copy(self.db_file, os.path.join(
            backup_out_dir, f"{db_name}.old.sqlite"))

        if self.debug:
            logger.info(f"Created backup db '{db_name}.old.sqlite'")
        tqdm.write(Fore.BLUE + f"Created backup db '{db_name}.old.sqlite'")

    def migrate_db(self):
        """ Migrates the db from old db schema to the new one
        """
        if os.path.isfile(self.input_db):
            self.db_file = self.input_db
            self.engine, self.SessionLocal = init_database(self.db_file)
        else:
            db_not_found_log(self.debug, self.input_db)
            sys.exit()
        # backup the db before migrating the data
        self.db_backup()
        self.db: Session = next(get_db(self.SessionLocal))
        if self.debug:
            logger.info("Migrating the database.")
        tqdm.write(Fore.GREEN + "Migrating the database.")
        try:
            crud.add_column(self.db)
        except sqlalchemy.exc.OperationalError:
            db_not_found_log(self.debug, self.db_file)
            sys.exit()

    def fetch_urls_from_page(self, fetch_urls: str):

        if self.debug:
            logger.debug("--fetch-urls flag used!")
            logger.info(f"Processing {fetch_urls}")

        with console.status(f"[bold green]Processing {fetch_urls}"):
            response = requests.get(fetch_urls, timeout=(5, 300))

            if self.debug:
                logger.debug(f"GET: {response.status_code}: {response.url}")

            html_page = BeautifulSoup(response.content, 'html.parser')

            found_flag = False
            if re.search("https://archiveofourown.org/", fetch_urls):
                ao3_series_works_html = []
                ao3_works_list = []
                ao3_series_list = []

                ao3_series_works_html_h4 = html_page.find_all(
                    'h4', attrs={'class': 'heading'})

                for i in ao3_series_works_html_h4:
                    ao3_series_works_html.append(i)

                ao3_series_works_html = ""
                for i in ao3_series_works_html_h4:
                    ao3_series_works_html += str(i)

                ao3_urls = BeautifulSoup(ao3_series_works_html, 'html.parser')

                for tag in ao3_urls.find_all('a', {'href': re.compile('/works/')}):
                    ao3_works_list.append(
                        "https://archiveofourown.org"+tag['href'])

                for tag in ao3_urls.find_all('a', {'href': re.compile('/series/')}):
                    ao3_series_list.append(
                        "https://archiveofourown.org"+tag['href'])

                if ao3_works_list:
                    found_flag = True
                    tqdm.write(Fore.GREEN +
                               f"\nFound {len(ao3_works_list)} works urls." +
                               Style.RESET_ALL)
                    ao3_works_list = '\n'.join(ao3_works_list)
                    tqdm.write(ao3_works_list + Fore.BLUE + "\n\nSaving the list to 'ao3_works_list.txt' in the current directory"
                               + Style.RESET_ALL)

                    with open("ao3_works_list.txt", "a") as f:
                        f.write(ao3_works_list+"\n")

                if ao3_series_list:
                    found_flag = True
                    tqdm.write(Fore.GREEN +
                               f"\nFound {len(ao3_series_list)} series urls." +
                               Style.RESET_ALL)
                    ao3_series_list = '\n'.join(ao3_series_list)
                    tqdm.write(ao3_series_list + Fore.BLUE + "\n\nSaving the list to 'ao3_series_list.txt' in the current directory"
                               + Style.RESET_ALL)

                    with open("ao3_series_list.txt", "a") as f:
                        f.write(ao3_series_list+"\n")

            if found_flag is False:
                tqdm.write(Fore.RED + "\nFound 0 urls.")
                self.exit_status = 1
