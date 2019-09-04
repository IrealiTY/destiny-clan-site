from datetime import datetime
import json
import os
import shutil
import sqlite3
import requests
import zipfile
from app import utilities
from app import models
from app import create_app
from app.utils import log
from config import Config

logger = log.get_logger(__name__)

def get_manifest():
    """
    Returns the current Destiny 2 API Manifest.
    Documentation: https://bungie-net.github.io/multi/operation_get_Destiny2-GetDestinyManifest.html#operation_get_Destiny2-GetDestinyManifest
    """
    manifest = utilities.http_get('https://bungie.net/Platform/Destiny2/Manifest/')
    return manifest

def get_manifest_url():
    """
    Returns the URL for the current Destiny 2 SQLITE database file.
    """
    manifest = get_manifest()
    manifest_db_name = manifest['Response']['mobileWorldContentPaths']['en']
    new_db_url = f'https://bungie.net{manifest_db_name}'
    return new_db_url

def update_check():
    """
    Checks the current manifest database URL from the API against the manifest database URL that we last downloaded.
    Returns false if the URL has not changed. Returns true if it has changed.
    """
    new_manifest = get_manifest_url()
    current_manifest = models.db.session.query(models.Manifest).first().url

    if current_manifest == new_manifest:
        print('No update found for the Manifest.')
        return False
    else:
        print('New Manifest available.')
        return True

def update(force=False):
    """Check if there is a new Manifest. If there is a new Manifest, update the database with the latest Manifest url."""
    if not force:
        manifest_check = update_check()
        if not manifest_check:
            print('No update found for the Manifest.')
            return
    else:
        print('Forcing Manifest update.')
    
    new_manifest = get_manifest_url()
    current_manifest = models.db.session.query(models.Manifest).first()
    current_manifest.url = new_manifest
    current_manifest.updated = datetime.now()

    try:
        models.db.session.commit()
        print('Manifest URL successfully updated in the database.')
    except Exception as e:
        models.db.session.rollback()
        print(f'Manifest URL was not updated in the database. Reason: {e}')
        return

    download_database()
    update_database()

def download_database():
    """
    Downloads the new content database and overwrites the old one.
    """

    print('Downloading new content database.')
    manifest_url = get_manifest_url()
    r = requests.get(manifest_url, headers=Config.BUNGIE_API_KEY, stream=True)
    with open('newdb.zip', 'wb') as f:
        for chunk in r.iter_content():
            f.write(chunk)

    print('New db downloaded to: newdb.zip')
    with zipfile.ZipFile('newdb.zip', 'r') as zip_ref:
        zip_ref.extractall('.')

    print('Extracting newdb.zip')

    files_in_dir = [f for f in os.listdir('.')]
    db_file = [f for f in files_in_dir if '.content' in f][0]

    print(f'DB extracted to {db_file}')
    current_directory = os.getcwd()
    src = os.path.join(current_directory, db_file)
    dst = os.path.join(current_directory, 'db.sqlite3')
    shutil.move(src, dst)
    
    print(f'{db_file} has been moved to db.sqlite3')

    file_to_delete = os.path.join(current_directory, 'newdb.zip')
    if os.path.isfile(file_to_delete):
        os.remove(file_to_delete)
        print('Deleted newdb.zip')

# TODO: Add code to add new database rows to postgres

def query_sqlite_database(query):
    sqlite_db_path = os.path.join(Config.PROJECT_ROOT, 'db.sqlite3')
    connection = sqlite3.connect(sqlite_db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    connection.close()
    return rows

def update_database():
    tables = [t[0] for t in query_sqlite_database("SELECT name FROM sqlite_master WHERE type='table';")]
    for table in tables:
        table_data = query_sqlite_database(f'SELECT * FROM {table}')
        for data in table_data:
            tbl = getattr(models, table)
            hash_id = str(data[0])
            data = json.loads(data[1])
            row = models.db.session.query(tbl).filter(tbl.hash==hash_id).first()
            if row:
                continue

            new = tbl(hash=hash_id, json=data)
            models.db.session.add(new)

            try:
                models.db.session.commit()
                logger.warning(f'{table}: successfully added hash {hash_id}')
            except Exception as e:
                logger.warning(f'{table}: failed to add hash {hash_id}. Reason: {e}')
                models.db.session.rollback()

    models.db.session.close()

def clean_database():
    """Delete all rows in every Definition table."""
    tables = [t[0] for t in query_sqlite_database("SELECT name FROM sqlite_master WHERE type='table';")]
    for table in tables:
        tbl = getattr(models, table)
        try:
            models.db.session.query(tbl).delete()
            models.db.session.commit()
            logger.warning(f'{table}: Successfully deleted all rows')

        except Exception as e:
            logger.warning(f'{table}: Failed to delete all rows')
            models.db.session.rollback()
