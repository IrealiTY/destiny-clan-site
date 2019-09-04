import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    db_url = 'postgresql://username:password@db:5432/swampfox'
    redis = 'sfredis'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or db_url_dev
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ROOT_DIR = os.path.dirname(__file__)
    DIST_DIR = os.path.join(ROOT_DIR, 'dist')
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    BUNGIE_API_KEY = {'X-API-Key': 'api key here'}

class ConfigProd(object):
    db_url = 'postgresql://username:password@db:5432/swampfox'
    redis = 'sfredis'
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ROOT_DIR = os.path.dirname(__file__)
    DIST_DIR = os.path.join(ROOT_DIR, 'dist')
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    BUNGIE_API_KEY = {'X-API-Key': 'api key here'}