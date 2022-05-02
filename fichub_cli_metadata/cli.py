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

import typer
import sys
import os
from loguru import logger
from datetime import datetime
from colorama import init, Fore, Style

from .utils.fetch_data import FetchData
from fichub_cli.utils.processing import get_format_type, check_cli_outdated
from fichub_cli_metadata import __version__

init(autoreset=True)  # colorama init
app = typer.Typer(add_completion=False)

# check if the cli is outdated
check_cli_outdated("fichub-cli-metadata", __version__)


# @logger.catch  # for internal debugging
@app.callback(no_args_is_help=True,
              invoke_without_command=True)
def metadata(
    input: str = typer.Option(
        "", "-i", "--input", help="Input: Either an URL or path to a file"),

    input_db: str = typer.Option(
        "", "--input-db", help="Use an existing sqlite db"),

    update_db: bool = typer.Option(
        False, "--update-db", help="Self-Update existing db (--input-db required)", is_flag=True),

    export_db: bool = typer.Option(
        False, "--export-db", help="Export the existing db as json (--input-db required)", is_flag=True),

    out_dir: str = typer.Option(
        "", "-o", "--out-dir", help="Path to the Output directory (default: Current Directory)"),

    download_ebook: str = typer.Option(
        "", "--download-ebook", help="Download the ebook as well. Specify the format: epub (default), mobi, pdf or html"),

    fetch_urls: str = typer.Option(
        "", help="Fetch all story urls found from a page. Currently supports archiveofourown.org only"),

    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Show fic stats", is_flag=True),

    force: bool = typer.Option(
        False, "--force", help="Force update the metadata", is_flag=True),

    debug: bool = typer.Option(
        False, "-d", "--debug", help="Show the log in the console for debugging", is_flag=True),

    changelog: bool = typer.Option(
        False, "--changelog", help="Save the changelog file", is_flag=True),

    debug_log: bool = typer.Option(
        False, "--debug-log", help="Save the logfile for debugging", is_flag=True),

    automated: bool = typer.Option(
        False, "-a", "--automated", help="For internal testing only",
        is_flag=True, hidden=True),

    version: bool = typer.Option(
        False, "--version", help="Display version & quit", is_flag=True)

):
    """
    A metadata plugin for fetching Metadata from the Fichub API for fichub-cli

    To report issues upstream for the supported sites, visit https://fichub.net/#contact

    To report issues for the plugin, open an issue at https://github.com/fichub-cli-contrib/fichub-cli-metadata/issues

    To report issues for the CLI, open an issue at https://github.com/FicHub/fichub-cli/issues

    Failed downloads will be saved in the `err.log` file in the current directory
    """

    if debug_log:
        timestamp = datetime.now().strftime("%Y-%m-%d T%H%M%S")
        logger.remove()  # remove all existing handlers
        logger.add(f"fichub_cli - {timestamp}.log")
        debug = True
        typer.echo(
            Fore.GREEN + "Creating " + Style.RESET_ALL + Fore.YELLOW +
            f"fichub_cli - {timestamp}.log" + Style.RESET_ALL +
            Fore.GREEN + " in the current directory!" + Style.RESET_ALL)

    if not download_ebook == "":
        format_type = get_format_type(download_ebook)
    else:
        format_type = None

    if input and not update_db:
        fic = FetchData(debug=debug, automated=automated, format_type=format_type,
                        out_dir=out_dir, input_db=input_db, update_db=update_db,
                        export_db=export_db, force=force, verbose=verbose,
                        changelog=changelog)
        fic.save_metadata(input)

    if input_db and update_db:

        fic = FetchData(debug=debug, automated=automated, format_type=format_type,
                        out_dir=out_dir, input_db=input_db, update_db=update_db,
                        export_db=export_db, force=force, verbose=verbose,
                        changelog=changelog)
        fic.update_metadata()

    if export_db:
        fic = FetchData(debug=debug, automated=automated, changelog=changelog,
                        out_dir=out_dir, input_db=input_db, update_db=update_db,
                        export_db=export_db, force=force, verbose=verbose)
        fic.export_db_as_json()

    if fetch_urls:
        fic = FetchData(debug=debug)
        fic.fetch_urls_from_page(fetch_urls)

    if version is True:
        from . import __version__
        typer.echo(f"fichub-cli-metadata: v{__version__}")

    try:
        if fic.exit_status == 1:
            typer.echo(
                Fore.RED +
                "\nThe CLI ran into some errors! Check " + Style.RESET_ALL +
                Fore.YELLOW + "err.log" + Style.RESET_ALL + Fore.RED +
                " in the current directory for urls!" + Style.RESET_ALL)

        if os.path.exists("output.log"):
            rm_output_log = typer.confirm(
                Fore.BLUE+"Delete the output.log?", abort=False, show_default=True)
            if rm_output_log is True:
                os.remove("output.log")

        sys.exit(fic.exit_status)

    # FileNotFoundError: output.log doesnt exist, when run 1st time
    # UnboundLocalError: 'fic' is not assigned value for --version flag
    except (FileNotFoundError, UnboundLocalError):
        sys.exit(0)
