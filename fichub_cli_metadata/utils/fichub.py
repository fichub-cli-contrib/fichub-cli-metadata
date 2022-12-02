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

import requests
from requests.adapters import HTTPAdapter

from colorama import Fore, Style
from tqdm import tqdm
from loguru import logger
import time
import re

from fichub_cli.utils.fichub import retry_strategy, FicHub as Fichub_Base
from fichub_cli import __version__ as core_version
from fichub_cli_metadata import __version__ as plugin_version

headers = {
    'User-Agent': f'fichub_cli_metadata/{plugin_version} (fichub_cli: {core_version})'
}


class FicHub(Fichub_Base):
    def __init__(self, debug, automated, exit_status):
        self.debug = debug
        self.automated = automated
        self.exit_status = exit_status
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.http = requests.Session()
        self.http.mount("https://", adapter)
        self.http.mount("http://", adapter)

    def get_fic_metadata(self, url: str, format_type: list):
        """ **OVERRIDING FUNCTION**\n
        Sends GET request to Fichub API to fetch the metadata
        """
        params = {'q': url}
        if self.automated:  # for internal testing
            params['automated'] = 'true'
            if self.debug:
                logger.debug(
                    "--automated flag was passed. Internal Testing mode is on.")

        for _ in range(2):
            try:
                response = self.http.get(
                    "https://fichub.net/api/v0/epub", params=params,
                    allow_redirects=True, headers=headers, timeout=(6.1, 300)
                )
                if self.debug:
                    logger.debug(
                        f"GET: {response.status_code}: {response.url}")
                    if self.automated:
                        logger.debug(
                            f"Headers: {response.request.headers}")
                break
            except (ConnectionError, TimeoutError, Exception) as e:
                if self.debug:
                    logger.error(str(e))
                tqdm.write("\n" + Fore.RED + str(e) + Style.RESET_ALL +
                           Fore.GREEN + "\nWill retry in 3s!" +
                           Style.RESET_ALL)
                time.sleep(3)

        try:
            self.response = response.json()
            self.fic_metadata = self.response['meta']

            self.file_format =[]
            self.cache_hash = {}
            cache_urls= {}

            for format in format_type:
                if format == 0:
                    cache_urls['epub'] = self.response['urls']['epub']
                    self.cache_hash['epub'] = self.response['hashes']['epub']
                    self.file_format.append(".epub")

                elif format == 1:
                    cache_urls['mobi'] = self.response['urls']['mobi']
                    self.cache_hash['mobi'] = self.response['hashes']['epub']
                    self.file_format.append(".mobi")

                elif format == 2:
                    cache_urls['pdf'] = self.response['urls']['pdf']
                    self.cache_hash['pdf'] = self.response['hashes']['epub']
                    self.file_format.append(".pdf")

                elif format == 3:
                    cache_urls['zip'] =self.response['urls']['html']
                    self.cache_hash['zip'] = self.response['hashes']['epub']
                    self.file_format.append(".zip")
            
            self.files = {}
            for file_format in self.file_format:
                self.files[self.response['urls']['epub'].split(
                "/")[4].split("?")[0].replace(".epub", file_format)] = {
                "hash":self.cache_hash[file_format.replace(".","")],
                "download_url": "https://fichub.net"+cache_urls[file_format.replace(".","")]
                }

        # Error: 'epub_url'
        # Reason: Unsupported URL
        except (KeyError, UnboundLocalError) as e:
            if self.debug:
                logger.error(f"Error: {str(e)} not found!")
                logger.error(
                    f"Skipping unsupported URL: {url}")

            self.exit_status = 1
            tqdm.write(
                Fore.RED + f"\nSkipping unsupported URL: {url}" +
                Style.RESET_ALL + Fore.CYAN +
                "\nTo see the supported site list, use " + Fore.YELLOW +
                "fichub_cli -ss" + Style.RESET_ALL + Fore.CYAN +
                "\nReport the error if the URL is supported!\n")
