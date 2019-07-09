import json
from redis_queue import RedisQueue
from app import create_app
from app.destiny.client import DestinyAPI

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    d2 = DestinyAPI()
    q = RedisQueue('playerstats')

    clan_members = d2.get_clan_members_api()
    for clan_member in clan_members:
        q.put(json.dumps(clan_member))
