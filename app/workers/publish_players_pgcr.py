import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from app.destiny.client import DestinyAPI
from app.redis import redis_queue
from app.utils import log

def main():
    queue = 'pgcr_players'
    modes = [4, 5]
    q = redis_queue.get_redis_queue(queue)

    clan_members = d2.get_clan_members_api()
    for mode in modes:
        for clan_member in clan_members:
            clan_member['mode'] = mode
            try:
                q.put(json.dumps(clan_member))
                logger.debug(f'Sending data to Redis queue {queue}: {clan_member}')
            except Exception:
                logger.warning('Failed to connect to Redis while executing PUT request. Reconnecting.')
                q = redis_queue.get_redis_queue(queue)
                continue

if __name__ == "__main__":
    logger = log.get_logger(__name__)
    app = create_app()
    app.app_context().push()
    d2 = DestinyAPI()
    main()
