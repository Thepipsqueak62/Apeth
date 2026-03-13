import configparser
import os.path

from FlintCore.src.utils.config_utils import create_config_ini


def read_config():
    config = configparser.ConfigParser()

    if not os.path.exists('settings.ini'):
        print("No settings.ini found")
        print("Creating settings.ini...")
        create_config_ini()

    config.read('settings.ini')
    return config

