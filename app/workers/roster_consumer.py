import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from app.destiny.client import DestinyAPI
from app.redis import redis_queue
from app.utils import log

def main():
    q = redis_queue.get_redis_queue('playerstats')
    while True:
        if q.empty():
            logger.debug('Playerstats queue is empty')
            exit

        try:
            player = q.get()
        except Exception:
            logger.exception('Failed to connect to issue Redis command. Reconnecting.')
            q = redis_queue.get_redis_queue('playerstats')
            continue

        player = player.decode('utf-8')
        player = json.loads(player)
        membership_id = player['membershipId']
        platform = player['membershipType']
        status = player['isOnline']

        try:
            d2.db_update_stats(membership_id, platform, status)
        except Exception:
            logger.exception(f'Failed to update player {membership_id}. Platform: {platform} | Online: {status}')

if __name__ == "__main__":
    logger = log.get_logger(__name__)
    app = create_app()
    app.app_context().push()
    d2 = DestinyAPI()
    main()
