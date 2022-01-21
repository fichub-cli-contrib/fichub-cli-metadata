    import os
import json
from loguru import logger

from appdirs import user_data_dir


appname = "fichub_cli"
appauthor = "fichub"

app_dir = user_data_dir(appname, appauthor)
metadata_dir = os.path.join(app_dir, 'metadata')


class Settings:
    def __init__(self):
        pass

    def init_app(self):

        dir_list = [metadata_dir]

        # create the directories
        for _dir in dir_list:
            try:
                os.makedirs(_dir)
            except FileExistsError:
                pass
