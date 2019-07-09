import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    db_url_dev = 'postgresql://username:password@db.lab.local:5432/swampfox'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or db_url_dev
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BUNGIE_API_KEY = {'X-API-Key': 'api key here'}
    ROOT_DIR = os.path.dirname(__file__)
    DIST_DIR = os.path.join(ROOT_DIR, 'dist')

class ConfigProd(object):
    db_url = 'postgresql://username:password@db.lab.local:5432/swampfoxprod'
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BUNGIE_API_KEY = {'X-API-Key': 'api key here'}
