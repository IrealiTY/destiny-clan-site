from datetime import datetime
import os
import sys
import json
import logging
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
    q = RedisQueue('players')
    q_matches = RedisQueue('matches')

    while True:
        if q.empty():
            exit

        player = q.get()
        player = player.decode('utf-8')
        data = d2.get_new_matches(player['membershipId'])
        if data:
            logging.info(f'COLLECTOR ({pid}) | ', data)
            q_matches.put(json.dumps(data))