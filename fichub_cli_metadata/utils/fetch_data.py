import os
import sys
import shutil
from datetime import datetime
import sqlalchemy
from tqdm import tqdm
from colorama import Fore, Style
from loguru import logger
from rich.console import Console

from sqlalchemy.orm import Session

from .fichub import FicHub
from .logging import meta_fetched_log, db_not_found_log
from . import models, crud
from .processing import init_database, get_db, object_as_dict

from fichub_cli.utils.logging import download_processing_log
from fichub_cli.utils.processing import check_url


bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt}, {rate_fmt}{postfix}, ETA: {remaining}"
console = Console()


class FetchData:
    def __init__(self, out_dir="", input_db="", update_db=False,
                 export_db=False, debug=False, automated=False, force=False):
        self.out_dir = out_dir
        self.input_db = input_db
        self.update_db = update_db
        self.export_db = export_db
        self.force = force
        self.debug = debug
        self.automated = automated
        self.exit_status = 0

    def save_metadata(self, input: str):
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
                urls = f.read().splitlines()

        else:
            if self.debug:
                logger.info("Input is an URL")
            urls = [input]

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
            # for 1st time use, no db exists
            pass
        with tqdm(total=len(urls), ascii=False,
                  unit="url", bar_format=bar_format) as pbar:

            for url in urls:
                download_processing_log(self.debug, url)
                pbar.update(1)
                supported_url, self.exit_status = check_url(
                    url, self.debug, self.exit_status)

                if supported_url:

                    if self.input_db:
                        exists = self.db.query(models.Metadata).filter(
                            models.Metadata.source == url).first()
                    else:
                        exists = None
                    if not exists or self.force:
                        fic = FicHub(self.debug, self.automated,
                                     self.exit_status)
                        fic.get_fic_extraMetadata(url)
                        if fic.fic_extraMetadata:
                            meta_fetched_log(self.debug, url)
                            self.save_to_db(fic.fic_extraMetadata)

                            # update the exit status
                            self.exit_status = fic.exit_status
                        else:
                            self.exit_status = 1
                            supported_url = None
                    else:
                        self.exit_status = 1
                        supported_url = None
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

    def save_to_db(self, item):
        try:
            models.Base.metadata.create_all(bind=self.engine)
        except sqlalchemy.exc.OperationalError:
            db_not_found_log(self.debug, self.db_file)
            sys.exit()

        # if force=True, dont insert, skip to else & update instead
        if not self.update_db and not self.force:
            crud.insert_data(self.db, item, self.debug)

        elif self.update_db and not self.input_db == "" or self.force:
            crud.update_data(self.db, item, self.debug)

    def update_metadata(self):
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

        # backup the db before changing the data
        self.db_backup()
        with tqdm(total=len(all_rows), ascii=False,
                  unit="url", bar_format=bar_format) as pbar:

            for row in all_rows:
                row_dict = object_as_dict(row)
                pbar.update(1)
                fic = FicHub(self.debug, self.automated,
                             self.exit_status)
                fic.get_fic_extraMetadata(row_dict['source'])

                if fic.fic_extraMetadata:
                    meta_fetched_log(self.debug, row_dict['source'])
                    crud.update_data(
                        self.db, fic.fic_extraMetadata, self.debug)

                    # update the exit status
                    self.exit_status = fic.exit_status
                else:
                    self.exit_status = 1

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
            logger.info(f"Created backup db at {db_name}.old.sqlite")
        tqdm.write(Fore.BLUE + f"Created backup db as {db_name}.old.sqlite")
