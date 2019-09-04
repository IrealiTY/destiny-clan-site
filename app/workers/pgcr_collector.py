import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from app.destiny.client import DestinyAPI
from app.redis import redis_queue
from app.utils import log

def main():
    queue_players = 'pgcr_players'
    queue_matches = 'pgcr_matches'
    q_players = redis_queue.get_redis_queue(queue_players)
    q_matches = redis_queue.get_redis_queue(queue_matches)

    while True:
        try:
            if q_players.empty():
                exit

            player = q_players.get()
        except Exception as e:
            logger.warning(f'Failed to connect to Redis while executing BLPOP command. Reconnecting. Reason: {e}')
            q_players = redis_queue.get_redis_queue(queue_players)
            continue

        player = player.decode('utf-8')
        player = json.loads(player)
        membership_id = player['membershipId']
        platform = player['membershipType']
        mode = player['mode']

        try:
            data = d2.get_new_matches(membership_id, platform, mode)
        except Exception as e:
            logger.warning(f'{membership_id}:{platform}:{mode} Failed to retrieve check for new PGCRs. Reason: {e}')
            continue

        if data:
            if data['characters']:
                for character in data['characters']:
                    for pgcr in character['matches']:
                        match = {
                            'membershipId': membership_id,
                            'membershipType': platform,
                            'characterId': character['characterId'],
                            'mode': mode,
                            'match': pgcr
                        }

                        try:
                            q_matches.put(json.dumps(match))
                        except Exception as e:
                            logger.warning(f'{membership_id}:{platform}:{mode} Failed to connect to Redis while executing PUT command. Reconnecting. Reason: {e}')
                            q_matches = redis_queue.get_redis_queue(queue_matches)
                            continue

if __name__ == "__main__":
    logger = log.get_logger(__name__)
    app = create_app()
    app.app_context().push()
    d2 = DestinyAPI()
    main()