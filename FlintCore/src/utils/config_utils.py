from FlintCore.src.utils.config_structure import config


def create_config_ini():
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

