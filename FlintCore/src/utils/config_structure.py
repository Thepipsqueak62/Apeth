import configparser

config = configparser.ConfigParser()

config['database'] = {
    'engine': 'sqlite',
    'path':'test.db',
    'host': 'localhost',
    'port': 5000,
    'debug': False,
    'username': 'admin',
    'password': 'root',
}
config['Entities'] = {
    'sleep': '5',
    'jitter': '1000',
    'max_retries': '3'
}

config['Crypto'] = {
    'key': 'supersecretkey',
    'algorithm': 'AES256'
}
