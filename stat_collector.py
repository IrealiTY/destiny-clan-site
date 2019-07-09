import json
import logging
import os
import sys
from redis_queue import RedisQueue
from app import create_app
from app.destiny.client import DestinyAPI

logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

if __name__ == "__main__":
    pid = os.getpid()
    app = create_app()
    app.app_context().push()
    d2 = DestinyAPI()
    q = RedisQueue('playerstats')

    while True:
        if q.empty():
            logging.info(f'Queue empty')
            exit

        player = q.get()
        player = player.decode('utf-8')
        player = json.loads(player)
        membership_id = player['membershipId']
        platform = player['membershipType']
        status = player['isOnline']

        try:
            d2.db_update_stats(membership_id, platform, status)
        except Exception as e:
            logging.error(f'Failed to update player {membership_id} (Platform: {platform} | Online: {status}). Reason: {e}')

