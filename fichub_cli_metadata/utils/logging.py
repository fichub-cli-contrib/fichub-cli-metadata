from colorama import Fore
from loguru import logger
from tqdm import tqdm


def meta_fetched_log(debug: bool, url: str):
    if debug:
        logger.info(f"Metadata fetched for {url}")
    else:
        tqdm.write(Fore.GREEN + f"Metadata fetched for {url}")


def db_not_found_log(debug: bool, input_db: str):
    tqdm.write(
        Fore.RED + f"Unable to open database file: {input_db}\nPlease recheck the filename!")
    if debug:
        logger.error(
            f"Unable to open database file: {input_db}\nPlease recheck the filename!")
