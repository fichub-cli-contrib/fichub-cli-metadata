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

import sys
import os
from loguru import logger
from datetime import datetime
from colorama import init, Fore, Style

from .utils.fetch_data import FetchData

init(autoreset=True)  # colorama init
timestamp = datetime.now().strftime("%Y-%m-%d T%H%M%S")

# @logger.catch  # for internal debugging


def metadata(
    input: str = typer.Option(
        "", "-i", "--input", help="Input: Either an URL or path to a file"),

    input_db: str = typer.Option(
        "", "--input-db", help="Use an existing sqlite db"),

    update_db: bool = typer.Option(
        False, "--update-db", help="Self-Update existing db (--input-db required)", is_flag=True),

    export_db: bool = typer.Option(
        False, "--export-db", help="Export the existing db as json (--input-db required)", is_flag=True),

    migrate_db: bool = typer.Option(
        False, "--migrate-db", help="Migrate to new db schema (--input-db required)", is_flag=True),

    out_dir: str = typer.Option(
        "", "-o", "--out-dir", help="Path to the Output directory (default: Current Directory)"),

    force: bool = typer.Option(
        False, "--force", help="Force update the metadata", is_flag=True),

    debug: bool = typer.Option(
        False, "-d", "--debug", help="Show the log in the console for debugging", is_flag=True),

    log: bool = typer.Option(
        False, help="Save the logfile for debugging", is_flag=True),

    automated: bool = typer.Option(
        False, "-a", "--automated", help="For internal testing only", is_flag=True, hidden=True),

    version: bool = typer.Option(
        False, help="Display version & quit", is_flag=True)


):
    """
    A metadata plugin for fetching Metadata from the Fichub API for fichub-cli

    To report issues upstream for the supported sites, visit https://fichub.net/#contact

    To report issues for the plugin, open an issue at https://github.com/fichub-cli-contrib/fichub-cli-metadata/issues

    To report issues for the CLI, open an issue at https://github.com/FicHub/fichub-cli/issues

    Failed downloads will be saved in the `err.log` file in the current directory
    """
    if log is True:
        # debug = True
        typer.echo(
            Fore.GREEN + "Creating " + Style.RESET_ALL + Fore.YELLOW +
            f"fichub_cli - {timestamp}.log" + Style.RESET_ALL +
            Fore.GREEN + " in the current directory!" + Style.RESET_ALL)
        logger.add(f"fichub_cli - {timestamp}.log")

    if input and not update_db:
        fic = FetchData(debug=debug, automated=automated,
                        out_dir=out_dir, input_db=input_db, update_db=update_db,
                        export_db=export_db, force=force)
        fic.save_metadata(input)

    if input_db and update_db:
        fic = FetchData(debug=debug, automated=automated,
                        out_dir=out_dir, input_db=input_db, update_db=update_db,
                        export_db=export_db, force=force)
        fic.update_metadata()

    if export_db:
        fic = FetchData(debug=debug, automated=automated,
                        out_dir=out_dir, input_db=input_db, update_db=update_db,
                        export_db=export_db, force=force)
        fic.export_db_as_json()

    if input_db and migrate_db:
        fic = FetchData(debug=debug, automated=automated,
                        out_dir=out_dir, input_db=input_db, update_db=update_db,
                        export_db=export_db, force=force)
        fic.migrate_db()

    if version is True:
        typer.echo("fichub-cli-metadata: v0.1.3")

    try:
        if os.path.exists("output.log"):
            rm_output_log = typer.prompt(
                Fore.BLUE+"Delete the output.log?(y/n)")
            if rm_output_log == 'y':
                os.remove("output.log")

    # output.log doesnt exist, when run 1st time
    except FileNotFoundError:
        pass

    try:
        if fic.exit_status == 1:
            typer.echo(
                Fore.RED +
                "\nMetadata fetch failed for one or more URLs! Check " + Style.RESET_ALL +
                Fore.YELLOW + "err.log" + Style.RESET_ALL + Fore.RED +
                " in the current directory for urls!" + Style.RESET_ALL)
        sys.exit(fic.exit_status)
    except UnboundLocalError:
        sys.exit(0)
