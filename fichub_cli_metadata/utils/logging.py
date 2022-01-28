from colorama import Fore
from loguru import logger
from tqdm import tqdm


def meta_fetched_log(debug: bool, url: str):
    if debug:
        logger.info(f"Metadata fetched for {url}")
    else:
        tqdm.write(Fore.GREEN + f"Metadata fetched for {url}")
