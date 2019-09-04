import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from app.destiny.client import DestinyAPI
from app.redis import redis_queue
from app.utils import log

def main():
    queue = 'pgcr_matches'
    q = redis_queue.get_redis_queue(queue)
    while True:
        try:
            if q.empty():
                exit

            data = q.get()
        except Exception as e:
            logger.warning(f'Failed to connect to Redis while executing BLPOP. Reconnecting. Reason: {e}')
            q = redis_queue.get_redis_queue(queue)
            continue

        logger.debug(f'Data pulled from redis: {data}')
        data = data.decode('utf-8')
        data = json.loads(data)
        player = data['membershipId']
        platform = data['membershipType']
        character = data['characterId']
        mode = data['mode']
        match = data['match']

        try:
            d2.db_store_pgcr(player, character, match, mode)
        except Exception as e:
            logger.warning(f'{player}:{platform}:{character_id}:{mode} Error storing PGCR {match}. Reason: {e}')

if __name__ == "__main__":
    logger = log.get_logger(__name__)
    app = create_app()
    app.app_context().push()
    d2 = DestinyAPI()
    main()
