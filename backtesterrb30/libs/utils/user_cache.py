import os
from appdirs import user_cache_dir
import shutil

TEMP_CACHE_DIR = "./.temp_rb30_cache"


def configure_cache_dir(skip_cache: False) -> str:
    if skip_cache:
        dir = TEMP_CACHE_DIR
        if not os.path.exists(dir):
            os.makedirs(dir)
        else:
            shutil.rmtree(dir)
            os.makedirs(dir)
        return dir
    return user_cache_dir("rb30_cache")
