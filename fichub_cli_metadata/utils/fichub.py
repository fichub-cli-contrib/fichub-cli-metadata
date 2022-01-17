import requests
import re
from colorama import Fore, Style
from tqdm import tqdm
from loguru import logger
import json

headers = {
    'User-Agent': 'fichub_cli_metadata/0.1',
}


class FicHub:
    def __init__(self, debug, automated, exit_status):
        self.debug = debug
        self.automated = automated
        self.exit_status = exit_status

    def get_fic_extraMetadata(self, url: str):

        params = {'q': url}
        if self.automated:  # for internal testing
            params['automated'] = 'true'
            if self.debug:
                logger.debug(
                    "--automated flag was passed. Internal Testing mode is on.")

        response = requests.get(
            "https://fichub.net/api/v0/epub", params=params,
            allow_redirects=True, headers=headers
        )

        if self.debug:
            logger.debug(f"GET: {response.status_code}: {response.url}")

        try:
            self.response = response.json()
            self.fic_extraMetadata = json.dumps(
                self.response['meta'], indent=4)

        # if metadata not found
        except KeyError:
            self.fic_extraMetadata = ""
            tqdm.write(
                Fore.RED + f"Skipping unsupported URL: {url}" +
                Style.RESET_ALL + Fore.CYAN +
                "\nReport the error if the URL is supported!")
