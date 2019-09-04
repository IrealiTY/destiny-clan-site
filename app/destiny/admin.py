"""Aministration functions (adding new clan members, removing clan members that have left, etc)"""

from app import utilities
from app import models
from app.destiny import client
from app.utils import log

logger = log.get_logger(__name__)
CLAN_ID = 198175

def get_clan_member_ids():
    """
    Returns a list of membership_id's from the API for all the characters in the provided clan id.
    """
    clan = utilities.http_get(f'https://bungie.net/Platform/GroupV2/{CLAN_ID}/Members/')
    return [clan_member['destinyUserInfo']['membershipId'] for clan_member in clan['Response']['results']] if clan else None

def db_get_clan_member_ids():
    """
    Returns a list of membership_id's from our DB for all clan members.
    """
    ids = [clan_member.membership_id for clan_member in models.db.session.query(models.Players).all()]
    return ids

# Should this be our 'check if all current clan members from the API match the current clan members in the DB' function? If so, rename it.
def get_former_clan_members():
    """
    Returns a list of clan members that exist in the database but are no longer in the clan (via API).
    """
    current_members_api = get_clan_member_ids()
    current_members_db = db_get_clan_member_ids()
    former_members = list(set(current_members_db).difference(current_members_api))
    for member in former_members:
        player = models.db.session.query(models.Players).filter(models.Players.membership_id==member).first()
        if player:
            name = player.name
            logger.warning(f'{member}:{name} has left the clan')

    return former_members if former_members else None

def db_remove_former_clan_members():
    members_to_delete = get_former_clan_members()
    if not members_to_delete:
        return
    
    for member in members_to_delete:
        logger.warning(f'{member}: Deleting player from database')
        chars_to_delete = [char.id for char in models.db.session.query(models.Characters).join(models.Players).filter(models.Players.membership_id==member).all()]

        # Delete all weapons for every character
        for char in chars_to_delete:
            models.db.session.query(models.WeaponsData).filter(models.WeaponsData.parent_id==char).delete()
            models.db.session.commit()

        for char in chars_to_delete:
            models.db.session.query(models.PostGameCarnageReport).filter(models.PostGameCarnageReport.parent_character==char).delete()
            models.db.session.commit()

        for char in chars_to_delete:
            models.db.session.query(models.RaidStats).filter(models.RaidStats.parent_char==char).delete()
            models.db.session.commit()

        # Delete all characters that the Player has
        for char in chars_to_delete:
            models.db.session.query(models.Characters).filter(models.Characters.id==char).delete()
            models.db.session.commit()

        player_id = models.db.session.query(models.Players).filter(models.Players.membership_id==member).first().id

        # Delete collectibles associated with the player
        models.db.session.query(models.CollectiblesPlayer).filter(models.CollectiblesPlayer.parent_player==player_id).delete()
        models.db.session.commit()

        # Delete stats associated with the player
        models.db.session.query(models.Stats).filter(models.Stats.parent_player==player_id).delete()
        models.db.session.commit()

        # Delete Player
        models.db.session.query(models.Players).filter(models.Players.membership_id==member).delete()
        models.db.session.commit()

def db_update_clan_members():
    """
    Fetch the current clan roster from the API and store the new members in the database.
    """
    clan = utilities.http_get(f'https://bungie.net/Platform/GroupV2/{CLAN_ID}/Members/')
    if not clan:
        return

    for clan_member in clan['Response']['results']:
        player_name = clan_member['destinyUserInfo']['displayName']
        player_id = str(clan_member['destinyUserInfo']['membershipId'])
        platform = clan_member['destinyUserInfo']['membershipType']
        date_joined = clan_member['joinDate']
        player_check = models.db.session.query(models.Players).filter(models.Players.membership_id==player_id).first()
        if not player_check:
            print(f'{player_name}:{player_id} New player')
            new = models.Players(name=player_name, membership_id=player_id, membership_type=platform, join_date=date_joined)
            models.db.session.add(new)
            try:
                models.db.session.commit()
            except Exception as e:
                model.db.session.rollback()
                logger.warning(f'{player_id}:{player_name} Error comitting new clan member to database. Reason: {e}')

def db_update_characters():
    """
    Updates the database with all characters in the clan.
    Queries the API to: get all clan members -> get all characters for each member -> stores in db
    Each row for a character has a reference back to its Player.
    """
    d2 = client.DestinyAPI()
    player_ids = db_get_clan_member_ids()
    for player in player_ids:
        # TODO: Technically this would be bad if someone was to delete a char and recreate it but whatever
        player_chars_in_db = [char.char_id for char in models.db.session.query(models.Characters).join(models.Players).filter(models.Players.membership_id==player).all()]
        if len(player_chars_in_db) == 3:
            continue

        # We need to fetch the db object so that we can .append to it later in the function
        _player = models.db.session.query(models.Players).filter(models.Players.membership_id==f'{player}').first()
        _id = int(_player.membership_id)
        player_chars = d2.get_characters(_id, _player.membership_type)
        if not player_chars:
            print('No chars returned. Skipping.')
            continue
        
        if len(player_chars_in_db) == len(player_chars):
            continue

        for char in player_chars:
            if char not in player_chars_in_db:
                print(f'{_player.name} ({_player.membership_id}): Adding new character {char}')
                _character = d2.get_character(_id, _player.membership_type, char)
                _power = _character['Response']['character']['data']['light']
                class_hash = _character['Response']['character']['data']['classHash']
                _class_name = d2.get_definition('DestinyClassDefinition', class_hash)
                char_class = _class_name['displayProperties']['name']
                new = models.Characters(char_id=char, class_name=char_class, power=_power, last_pvp_match=0)
                _player.children.append(new)

    try:
        models.db.session.commit()
    except Exception as e:
        models.db.session.rollback()
