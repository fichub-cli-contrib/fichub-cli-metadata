import os
from datetime import datetime
from tqdm import tqdm
from colorama import Fore, Style
from loguru import logger
from rich.console import Console
import typer

from sqlalchemy.orm import Session

from .fichub import FicHub
from .logging import meta_fetched_log
from . import models, crud
from .processing import init_database, get_db

from fichub_cli.utils.logging import download_processing_log
from fichub_cli.utils.processing import check_url


bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt}, {rate_fmt}{postfix}, ETA: {remaining}"
console = Console()


class FetchData:
    def __init__(self, out_dir="", input_db="", update_db=False,
                 export_db=False, debug=False, automated=False):
        self.out_dir = out_dir
        self.input_db = input_db
        self.update_db = update_db
        self.export_db = export_db
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

        with tqdm(total=len(urls), ascii=False,
                  unit="url", bar_format=bar_format) as pbar:

            for url in urls:
                download_processing_log(self.debug, url)
                pbar.update(1)
                supported_url, self.exit_status = check_url(
                    url, self.debug, self.exit_status)

                if supported_url:
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

            if self.exit_status == 0:
                tqdm.write(Fore.GREEN +
                           "\nMetadata saved as " + Fore.BLUE +
                           f"{os.path.abspath(self.db_file)}"+Style.RESET_ALL +
                           Style.RESET_ALL)

    def save_to_db(self, item):
        self.db: Session = next(get_db(self.SessionLocal))
        models.Base.metadata.create_all(bind=self.engine)

        if not self.update_db:
            crud.insert_data(self.db, item, self.debug)

        elif self.update_db and not self.input_db == "":
            crud.update_data(self.db, item, self.debug)

    def export_db_as_json(self):
        _, file_name = os.path.split(self.input_db)
        self.db_name = os.path.splitext(file_name)[0]
        self.json_file = os.path.join(self.out_dir, self.db_name)+".json"
        self.engine, self.SessionLocal = init_database(self.input_db)

        if self.input_db:
            self.db: Session = next(get_db(self.SessionLocal))
            crud.dump_json(self.db, self.json_file, self.debug)
        else:
            typer.echo(
                "SQLite db is not found. Use an existing sqlite db using: --input-db ")
