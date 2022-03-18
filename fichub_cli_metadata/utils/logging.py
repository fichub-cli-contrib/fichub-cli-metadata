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

from colorama import Fore
from loguru import logger
from tqdm import tqdm


def meta_fetched_log(debug: bool, url: str):
    if debug:
        logger.info(f"Metadata fetched for {url}")
    tqdm.write(Fore.GREEN + f"Metadata fetched for {url}")


def db_not_found_log(debug: bool, input_db: str):
    if debug:
        logger.error(
            f"Unable to open database file: '{input_db}'\nPlease recheck the filename!")
    tqdm.write(
        Fore.RED + f"Unable to open database file: '{input_db}'\nPlease recheck the filename!")
