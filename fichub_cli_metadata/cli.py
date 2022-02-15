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

import argparse
import sys
import os
from loguru import logger
from datetime import datetime
from colorama import init, Fore, Style

from .utils.fetch_data import FetchData
from fichub_cli.utils.processing import out_dir_exists_check

init(autoreset=True)  # colorama init
timestamp = datetime.now().strftime("%Y-%m-%d T%H%M%S")


def create_parser():
    cli_parser = argparse.ArgumentParser(prog='fichub-cli-metadata',
                                         description="""
A metadata plugin for fetching Metadata from the Fichub API for fichub-cli

To report issues upstream for the supported sites, visit https://fichub.net/#contact

To report issues for the plugin, open an issue at https://github.com/fichub-cli-contrib/fichub-cli-metadata/issues

To report issues for the CLI, open an issue at https://github.com/FicHub/fichub-cli/issues

Failed downloads will be saved in the `err.log` file in the current directory
    """, formatter_class=argparse.RawTextHelpFormatter)

    cli_parser.add_argument("-i", "--input", type=str, default="",
                            help="Input: Either an URL or path to a file")

    cli_parser.add_argument("--input-db", type=str, default="",
                            help="Use an existing sqlite db")

    cli_parser.add_argument("--update-db", action='store_true',
                            help="Self-Update existing db (--input-db required)")

    cli_parser.add_argument("--export-db",  action='store_true',
                            help="Export the existing db as json (--input-db required)")

    cli_parser.add_argument("--migrate-db",  action='store_true',
                            help="Migrate to new db schema (--input-db required)")

    cli_parser.add_argument("-o", "--out-dir", type=str, default="",
                            help="Path to the Output directory for files (default: Current Directory)")

    cli_parser.add_argument('--force', action='store_true',
                            help="Force overwrite of an existing file")

    cli_parser.add_argument("-d", "--debug", action='store_true',
                            help="Show the log in the console for debugging")

    cli_parser.add_argument("--log", action='store_true',
                            help="Save the logfile for debugging")

    cli_parser.add_argument("-a", "--automated", action='store_true',
                            help=argparse.SUPPRESS)

    cli_parser.add_argument("--version", action='store_true',
                            help="Display version & quit")

    return cli_parser


# @logger.catch  # for internal debugging
def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    parser = create_parser()
    args = parser.parse_args(argv)
    # if no args is given, invoke help
    if len(argv) == 0:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Check if the output directory exists if input is given
    if not args.out_dir == "":
        out_dir_exists_check(args.out_dir)

    if args.log is True:
        # debug = True
        print(
            Fore.GREEN + "Creating " + Style.RESET_ALL + Fore.YELLOW +
            f"fichub_cli - {timestamp}.log" + Style.RESET_ALL +
            Fore.GREEN + " in the current directory!" + Style.RESET_ALL)
        logger.add(f"fichub_cli - {timestamp}.log")

    if args.input and not args.update_db:
        fic = FetchData(debug=args.debug, automated=args.automated,
                        out_dir=args.out_dir, input_db=args.input_db,
                        update_db=args.update_db,
                        export_db=args.export_db, force=args.force)
        fic.save_metadata(args.input)

    if args.input_db and args.update_db:
        fic = FetchData(debug=args.debug, automated=args.automated,
                        out_dir=args.out_dir, input_db=args.input_db,
                        update_db=args.update_db,
                        export_db=args.export_db, force=args.force)
        fic.update_metadata()

    if args.export_db:
        fic = FetchData(debug=args.debug, automated=args.automated,
                        out_dir=args.out_dir, input_db=args.input_db, update_db=args.update_db,
                        export_db=args.export_db, force=args.force)
        fic.export_db_as_json()

    if args.input_db and args.migrate_db:
        fic = FetchData(debug=args.debug, automated=args.automated,
                        out_dir=args.out_dir, input_db=args.input_db,
                        update_db=args.update_db,
                        export_db=args.export_db, force=args.force)
        fic.migrate_db()

    if args.version is True:
        print("fichub-cli-metadata: v0.1.3")

    try:
        if os.path.exists("output.log"):
            rm_output_log = input(
                Fore.BLUE+"Delete the output.log(y/n)?")
            if rm_output_log == 'y':
                os.remove("output.log")

    # output.log doesnt exist, when run 1st time
    except FileNotFoundError:
        pass

    try:
        if fic.exit_status == 1:
            print(
                Fore.RED +
                "\nMetadata fetch failed for one or more URLs! Check " + Style.RESET_ALL +
                Fore.YELLOW + "err.log" + Style.RESET_ALL + Fore.RED +
                " in the current directory for urls!" + Style.RESET_ALL)
        sys.exit(fic.exit_status)
    except UnboundLocalError:
        sys.exit(0)
