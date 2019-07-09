from datetime import datetime
import json
from redis_queue import RedisQueue
from app import create_app
from app.destiny.client import DestinyAPI

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    d2 = DestinyAPI()
    q = RedisQueue('players')

    clan_members = d2.db_get_clan_members()
    for clan_member in clan_members:
        q.put(json.dumps({'membershipId': clan_member.membership_id, 'membershipType': clan_member.membership_type}))