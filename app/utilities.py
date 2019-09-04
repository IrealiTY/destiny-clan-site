import json
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from pathlib import Path
import re
import sys
from sqlalchemy.dialects import postgresql
from config import Config
from app.utils import log

logger = log.get_logger(__name__)

def requests_retry_session(retries=2, backoff_factor=1, status_forcelist=(502, 503, 504), session=None):
    # Until a better method can be found, we won't retry on 500 error codes because sometimes these codes are intentionally returned by the API
    session = session or requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update(Config.BUNGIE_API_KEY)
    return session

def http_get(url):
    try:
        request = requests_retry_session().get(url)
    except Exception as e:
        logger.warning(e)
        return

    data = json.loads(request.text)
    if 'ErrorCode' in data:
        if data['ErrorCode'] == 1665:
            logger.debug(f'Private profile {request.request.url} - Response: {data}')
            return 1665

        if data['ErrorCode'] != 1:
            logger.warning(f'Error fetching {request.request.url} - Response: {data}')
            return

    return data

def get_raw_sql(query):
    return re.sub('\n', '', str(query.statement.compile(dialect=postgresql.dialect())))

def save_file(data, filename, path=False):
    """
    Save JSON data to a file.
    """
    if path:
        file_name = filename + ".json"
        file_path = path / file_name
        with file_path.open('w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)
            full_path = file_path.absolute().as_posix()
            print(f'Data saved to file: {full_path}')
    else:
        with open(f'{filename}.json', 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)
            print(f'Data saved to file: {filename}.json')

def print_json(data):
    print(json.dumps(data, indent=4))