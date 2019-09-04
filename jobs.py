import argparse
from app.destiny import client
from app.destiny import admin
from app.destiny import manifest
from app import create_app

d2 = client.DestinyAPI()

def update_manifest():
    manifest.update()

def update_manifest_force():
    manifest.update(force=True)

def check_matches():
    d2.db_get_all_clan_stats()

def remove_former_members():
    admin.db_remove_former_clan_members()

def update_glory():
    d2.update_all_glory()

def add_members():
    admin.db_update_clan_members()
    admin.db_update_characters()

def update_collectibles():
    d2.get_collectible_exotic_weapons()

def download_pgcr_history_crucible():
    d2.download_pgcr_history_crucible('4611686018470721488', '2305843009354414197')

function_map = {
    'manifest': update_manifest,
    'manifest-force': update_manifest_force,
    'matches': check_matches,
    'removemembers': remove_former_members,
    'addmembers': add_members,
    'glory': update_glory,
    'collectibles': update_collectibles,
    'pgcr': download_pgcr_history_crucible
}

parser = argparse.ArgumentParser()
parser.add_argument('command', choices=function_map.keys())
args = parser.parse_args()
start = function_map[args.command]

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    start()