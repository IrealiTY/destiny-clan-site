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
    q = RedisQueue('matches')

    while True:
        data = q.get()
        if data:
            logging.info('CONSUMER | Data pulled from redis: ', data)
            data = data.decode('utf-8')
            data = json.loads(data)
        else:
            exit

        player = data['membershipId']
        platform = data['membershipType']
        logging.info(f'CONSUMER ({pid}): {player} | Processing player')

        if data['characters']:
            for character in data['characters']:
                character_id = character['characterId']
                logging.info(f'CONSUMER ({pid}): {player}:{character_id} | Processing character')

                for match in character['matches']:
                    logging.info(f'CONSUMER ({pid}): {player}:{character_id}:{match} Processing match')
                    d2.db_update_match(character_id, match)

        d2.update_player_last_updated(player)