import argparse
from app.destiny import client
from app import create_app

d2 = client.DestinyAPI()

def check_manifest():
    d2.get_new_manifest()

def check_matches():
    d2.db_get_all_clan_stats()

def remove_former_members():
    d2.db_remove_former_clan_members()

def update_glory():
    d2.update_all_glory()

def add_members():
    d2.db_update_clan_members(d2.CLAN_ID)
    d2.db_update_characters()

def update_collectibles():
    d2.get_collectible_exotic_weapons()

function_map = {
    'manifest': check_manifest,
    'matches': check_matches,
    'removemembers': remove_former_members,
    'addmembers': add_members,
    'glory': update_glory,
    'collectibles': update_collectibles
}

parser = argparse.ArgumentParser()
parser.add_argument('command', choices=function_map.keys())
args = parser.parse_args()
start = function_map[args.command]

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    start()