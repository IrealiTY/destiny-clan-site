from app import models
from datetime import datetime, timedelta
from pathlib import Path
import json
from flask import jsonify
from sqlalchemy import func
from config import Config, ConfigProd
from app import utilities
from app.utils import log

logger = log.get_logger(__name__)

class DestinyAPI(object):
    def __init__(self):
        self.WEAPON_TYPES = ['all', 'kinetic', 'energy', 'power']
        self.SWAMPFOX_ID = 198175
        self.CLAN_ID = self.SWAMPFOX_ID
        self.db = models.db
        self.players_schema = models.PlayersSchema(many=True)
        self.player_schema = models.PlayerSchema()
        self.player_weapon_schema = models.PlayerWeaponSchema(many=True)
        self.character_schema = models.CharacterSchema(many=True)
        self.weapon_kills_schema = models.WeaponKillsSchema(many=True)
        self.weapon_type_kills_schema = models.WeaponTypeKillsSchema(many=True)
        self.weapon_schema = models.WeaponSchema()
        self.collectible_schema = models.CollectibleSchema()
        self.collectibles_schema = models.CollectibleSchema(many=True)
        self.weapon_category_kills_schema = models.WeaponCategoryKillsSchema(many=True)

    def get_hash(self, _hash):
        """Return item hash."""
        _hash = int(_hash)
        if (_hash & (1 << (32 - 1))) != 0:
            _hash = _hash - (1 << 32)
        return _hash

    def get_definition(self, table, definition_hash, convert_hash=True):
        """
        Return data from the Destiny Database for a given hash.
        Test: tests/test_destiny.py/test_get_definition()
        """

        try:
            table = getattr(models, table)
        except Exception as e:
            logger.warning(f'{table} not found in models; cannot look up hash.')
            return

        if convert_hash:
            definition_hash = str(self.get_hash(definition_hash))
        else:
            definition_hash = str(definition_hash)

        query = self.db.session.query(table).filter(table.hash==definition_hash).first()

        if query:
            return query.json
        else:
            return

    def get_definitions(self, table):
        """Return all definitions in a table."""
        try:
            table = getattr(models, table)
        except Exception as e:
            logger.warning(f'{table} not found in models; cannot look up hash.')
            return

        query = self.db.session.query(table).all()
        if query:
            return query
        else:
            return

    # Section: Profiles
    def get_profile(self, membership_id, membership_type):
        """Retrieve a Player's profile without any extra components."""
        profile = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=100')
        return profile

    def get_profile_all(self, membership_id, membership_type):
        """Returns components for: player profile, characters, presentation nodes, records, and collectibles"""
        profile = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=100,700,900,200,204,800')
        return profile if profile else None

    def get_aggregate_activity_stats(self, membership_id, membership_type, character_id):
        stats = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Account/{membership_id}/Character/{character_id}/Stats/AggregateActivityStats/')
        return stats if stats else None

    def get_seal_dict(self):
        """Used to keep track of 'difficulty level' per Seal."""
        sealDict = {
            'Dredgen': {
                'url': 'https://bungie.net/common/destiny2_content/icons/59c2c744dca630140a8a01690e0d7fd9.png',
                'displayName': 'Dredgen',
                'difficulty': 2
            },
            'Wayfarer': {
                'url': 'https://bungie.net/common/destiny2_content/icons/885677894bf02b920ad48bfc60e1bbe2.png',
                'displayName': 'Wayfarer',
                'difficulty': 6
            },
            'Cursebreaker': {
                'url': 'https://bungie.net/common/destiny2_content/icons/8f755eb3a9109ed7adfc4a8b27871e7a.png',
                'displayName': 'Cursebreaker',
                'difficulty': 7
            },
            'Rivensbane': {
                'url': 'https://bungie.net/common/destiny2_content/icons/92d4e0eab5d4ab4f29eed35abe6d72d1.png',
                'displayName': 'Rivensbane',
                'difficulty': 3,
            },
            'Reckoner': {
                'url': 'https://bungie.net/common/destiny2_content/icons/c7d249682178891ed7e737e76e395765.png',
                'displayName': 'Reckoner',
                'difficulty': 4
            },
            'Shadow': {
                'url': 'https://bungie.net/common/destiny2_content/icons/2e3c60186f7aa64107d843ed697fad1f.png',
                'displayName': 'Shadow',
                'difficulty': 1
            },
            'Blacksmith': {
                'url': 'https://bungie.net/common/destiny2_content/icons/1a6e93e560351ceb4b5a3bb76504fed6.png',
                'displayName': 'Blacksmith',
                'difficulty': 5,
            },
            'Unbroken': {
                'url': 'https://bungie.net/common/destiny2_content/icons/d214b107e924ba2d2ac55719d48e0d27.png',
                'displayName': 'Unbroken',
                'difficulty': 9
            },
            'Chronicler': {
                'url': 'https://bungie.net/common/destiny2_content/icons/f7e108baecc867a8124dc8f6f0bd2b23.png',
                'displayName': 'Chronicler',
                'difficulty': 8
            },
            'MMXIX': {
                'url': 'https://www.bungie.net/common/destiny2_content/icons/c6074edd6d01d703000704ae95461895.png',
                'displayName': 'MMXIX',
                'difficulty': 3
            }
        }
        return sealDict

    # SECTION: PRESENTATION NODES / SEALS
    def get_seals(self, membership_id, profile):
        """Get all Seals that a Player owns and store them in the database."""
        if 'data' not in profile['Response']['profilePresentationNodes']:
            logger.debug(f'{membership_id}: profilePresentationNodes is private. Skipping seal check.')
            return

        obtained_seals = []
        seal_dict = self.get_seal_dict()
        ROOT_SEAL_HASH = 1652422747

        # All Seals are a children of the root node
        root_seal_node = self.get_definition('DestinyPresentationNodeDefinition', ROOT_SEAL_HASH)
        if not root_seal_node:
            logger.warning(f'{ROOT_SEAL_HASH}: failed to get root Seal node. Skipping seal check.')
            return

        # Get a list of presentation nodes for each seal
        seal_presentation_nodes = [str(node['presentationNodeHash']) for node in root_seal_node['children']['presentationNodes']]
        
        for node in seal_presentation_nodes:
            if node in profile['Response']['profilePresentationNodes']['data']['nodes']:

                # Current progress of the objective
                node_progress = profile['Response']['profilePresentationNodes']['data']['nodes'][node]['progressValue']

                # Required progress for the objective (if it's 6, then progressValue needs to be 6 for this to be completed)
                node_progress_completed = profile['Response']['profilePresentationNodes']['data']['nodes'][node]['completionValue']

                # Get the presentation node definition for the seal
                seal_presentation_node = self.get_definition('DestinyPresentationNodeDefinition', int(node))
                if seal_presentation_node['redacted']:
                    logger.info(f'Presentation Node {node} (Seal) is redacted')
                    continue

                # Get the title rewarded by the seal
                try:
                    title = self.get_definition('DestinyRecordDefinition', int(seal_presentation_node['completionRecordHash']))['titleInfo']['titlesByGender']['Male']
                except KeyError:
                    logger.warning(f'{seal_completion_record_hash}: Failed to pull title name')
                    return

                #print(f'{node}: {node_progress} / {node_progress_completed} ({title})')

                if node_progress == node_progress_completed:
                    obtained_seals.append(title)
            else:
                characters = [k for k,v in profile['Response']['characterPresentationNodes']['data'].items()]
                for character in characters:
                    node_progress = profile['Response']['characterPresentationNodes']['data'][character]['nodes'][node]['progressValue']
                    node_progress_completed = profile['Response']['characterPresentationNodes']['data'][character]['nodes'][node]['completionValue']
                    presentation_node = self.get_definition('DestinyPresentationNodeDefinition', int(node))

                    try:
                        title = self.get_definition('DestinyRecordDefinition', int(presentation_node['completionRecordHash']))['titleInfo']['titlesByGender']['Male']
                    except KeyError:
                        logger.warning(f'{presentation_node}: Failed to pull title name from DestinyRecordDefinition')
                        continue

                    #print(f'{node}: {node_progress} / {node_progress_completed} ({title})')
                    if node == '1002334440':
                        if node_progress == (node_progress_completed - 1):
                            obtained_seals.append(title)
                            break
                    else:
                        if node_progress == node_progress_completed:
                            obtained_seals.append(title)
                            break

        if obtained_seals:
            obtained_seals = list(set(obtained_seals))
            obtained_seals = sorted(obtained_seals, key=lambda x: seal_dict[x]['difficulty'], reverse=True)
            player = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
            if not player:
                return

            player.seals = ','.join(obtained_seals)
            try:
                self.db.session.commit()
            except Exception as e:
                self.db.session.rollback()

    def get_player_last_played(self, membership_id, membership_type):
        player_profile = self.get_profile(membership_id, membership_type)
        if player_profile['ErrorCode'] != 1:
            print(f'Error retrieving profile for {membership_id}')
            return

        return player_profile['Response']['profile']['data']['dateLastPlayed']

    def get_player_last_played_obj(self, membership_id, membership_type):
        player_profile = self.get_profile(membership_id, membership_type)
        last_played_string = player_profile['Response']['profile']['data']['dateLastPlayed']
        last_played_object = datetime.strptime(last_played_string, '%Y-%m-%dT%H:%M:%SZ')
        return last_played_object

    def db_update_player_last_played(self, membership_id, membership_type):
        """Updates the database with the time that the player last played from the API."""
        player = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        player.last_played = self.get_player_last_played_obj(membership_id, membership_type)
        self.db.session.commit()

    def get_all_player_kills(self):
        kills = self.db.session.query(models.Players.name, models.Players.membership_id, models.Players.last_played, func.sum(models.WeaponsData.kills).label("total_kills")) \
            .join(models.Characters) \
            .join(models.WeaponsData) \
            .group_by(models.Players.name, models.Players.membership_id) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        return kills

    def get_all_player_kills_range(self, days):
        date_range = datetime.now() - timedelta(days=days)
        kills = self.db.session.query(models.Players.name, models.Players.membership_id, func.sum(models.WeaponsData.kills).label("total_kills")) \
            .join(models.Characters) \
            .join(models.WeaponsData) \
            .group_by(models.Players.name, models.Players.membership_id) \
            .filter(models.WeaponsData.match_time >= date_range) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        return kills

    def get_top_weapon_by_subtype(self, subtype, page):
        weapon_type_results = self.db.session.query(models.Weapons.name, models.Weapons.gun_type, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
            .join(models.WeaponsData) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id, models.Weapons.gun_type) \
            .filter(models.Weapons.gun_type==subtype) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .paginate(page, 10, False)
        return weapon_type_results

    def get_top_weapon_by_subtype_days(self, subtype, page, days):
        if days == 0:
            weapon_type_results = self.db.session.query(models.Weapons.name, models.Weapons.gun_type, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .group_by(models.Weapons.name, models.Weapons.weapon_id, models.Weapons.gun_type) \
                .filter(models.Weapons.gun_type==subtype) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .paginate(page, 10, False)
            return weapon_type_results

        time_range = datetime.now() - timedelta(days=days)
        weapon_type_results = self.db.session.query(models.Weapons.name, models.Weapons.gun_type, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
            .join(models.WeaponsData) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id, models.Weapons.gun_type) \
            .filter(models.Weapons.gun_type==subtype) \
            .filter(models.WeaponsData.match_time >= time_range) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .paginate(page, 10, False)
        return weapon_type_results

    def api_get_weapon_category_kills(self, category, days):
        valid_categories = [weapon.gun_type for weapon in self.db.session.query(models.Weapons.gun_type).distinct()]
        if category not in valid_categories:
            return

        if days == 0:
            query = self.db.session.query(models.Weapons.name, models.Weapons.gun_type, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .group_by(models.Weapons.name, models.Weapons.weapon_id, models.Weapons.gun_type) \
                .filter(models.Weapons.gun_type==category) \
                .order_by(func.sum(models.WeaponsData.kills).desc())

            results = self.weapon_category_kills_schema.dump(query)
            return jsonify(results.data)

        time_range = datetime.now() - timedelta(days=days)
        query = self.db.session.query(models.Weapons.name, models.Weapons.gun_type, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
            .join(models.WeaponsData) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id, models.Weapons.gun_type) \
            .filter(models.Weapons.gun_type==category) \
            .filter(models.WeaponsData.match_time >= time_range) \
            .order_by(func.sum(models.WeaponsData.kills).desc())

        results = self.weapon_category_kills_schema.dump(query)
        return jsonify(results.data)
    
    def get_player_kills(self, membership_id, days):
        if days > 0:
            time_range = datetime.now() - timedelta(days=days)
            return self.db.session.query(models.Players.name, func.sum(models.WeaponsData.kills).label("total_kills")) \
                .join(models.Characters) \
                .join(models.WeaponsData) \
                .group_by(models.Players.name) \
                .filter(models.Players.membership_id==membership_id) \
                .filter(models.WeaponsData.match_time >= time_range) \
                .first()
        else:
            return self.db.session.query(models.Players.name, func.sum(models.WeaponsData.kills).label("total_kills")) \
                .join(models.Characters) \
                .join(models.WeaponsData) \
                .group_by(models.Players.name) \
                .filter(models.Players.membership_id==membership_id) \
                .first()

    def get_total_clan_kills(self):
        return self.db.session.query(func.sum(models.WeaponsData.kills).label('total_kills')).first()

    def get_character(self, membership_id, membership_type, character_id):
        """Retrieve a character from the API."""
        return utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/Character/{character_id}/?components=200')

    def get_player_vs_char_played_time(self, membership_id):
        characters = self.db_get_character_ids(membership_id)
        for character in characters:
            class_name = self.db.session.query(models.Characters).filter(models.Characters.char_id==character).first().class_name
            character_last_played = self.get_character(membership_id, character)['Response']['character']['data']['dateLastPlayed']
            print(f'{class_name} - last played: {character_last_played}')

        player_last_played = self.get_player_last_played(membership_id)
        player_name = self.db.session.query(models.Players).filter(models.Players.membership_id==f'{membership_id}').first().name
        print(f'{player_name} - last played: {player_last_played}')

    def db_get_total_weapons(self):
        '''
        Returns a count of the total number of weapons used in the Crucible by clan members.
        '''
        weapon_count = self.db.session.query(func.count(models.Weapons.id)).first()[0]
        return weapon_count

    # SECTION: Clan member management
    def db_get_total_characters(self):
        '''
        Returns a count of the total number of clan characters.
        '''
        character_count = self.db.session.query(func.count(models.Characters.id)).first()[0]
        return character_count

    def db_get_total_clan_members(self):
        '''
        Returns a count of the total number of clan members.
        '''
        clan_member_count = self.db.session.query(func.count(models.Players.id)).first()[0]
        return clan_member_count

    def db_get_clan_members(self):
        """
        Returns a list of all clan member query objects from the database.
        """
        return [player for player in self.db.session.query(models.Players).all()]

    def get_clan_members_api(self):
        clan = utilities.http_get(f'https://bungie.net/Platform/GroupV2/{self.CLAN_ID}/Members/')
        clan_members = []
        for member in clan['Response']['results']:
            if member['destinyUserInfo']['membershipId'] == 4611686018433937884:
                continue

            clan_members.append(
                {
                    'membershipId': member['destinyUserInfo']['membershipId'],
                    'membershipType': member['destinyUserInfo']['membershipType'],
                    'isOnline': member['isOnline']
                })

        return clan_members

    def get_clan_members(self):
        """
        7/2/2019 Delete
        """
        players = self.db.session.query(models.Players.name, models.Players.membership_id, models.Players.last_played, models.Players.triumph, func.sum(models.WeaponsData.kills).label("total_kills")) \
            .join(models.Characters) \
            .join(models.WeaponsData) \
            .group_by(models.Players.name, models.Players.membership_id, models.Players.last_played, models.Players.triumph) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        players = self.players_schema.dump(models.Players)
        return jsonify(players.data)

    def api_get_roster(self):
        """Returns stats for all players in the clan for the Clan Roster."""
        all_players = []
        players = self.db.session.query(models.Players.name, models.Players.membership_id, models.Players.last_activity, models.Players.last_activity_time, models.Players.triumph, models.Players.seals, models.Players.join_date, models.Players.online, models.Players.title, func.max(models.Characters.power).label("highest_power")) \
            .join(models.Characters) \
            .group_by(models.Players.name, models.Players.membership_id, models.Players.last_activity, models.Players.last_activity_time, models.Players.triumph, models.Players.seals, models.Players.join_date, models.Players.online, models.Players.title) \
            .order_by(func.max(models.Characters.power).label("highest_power").desc()) \
            .all()

        for player in players:
            data = DestinyPlayer(player=player).serialize()
            all_players.append(data)

        return all_players

    # Section: CRUCIBLE - GLORY
    def get_glory_ranking(self, membership_id, membership_type, character_id):
        """
        Returns the current Glory rating for a Player.
        """
        character_progression = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/Character/{character_id}/?components=202')
        if character_progression['ErrorStatus'] == 'SystemDisabled':
            print('API is under maintenance. Current glory has not been returned.')
            return False

        glory = character_progression['Response']['progressions']['data']['progressions']['2679551909']['currentProgress']
        return glory

    def db_get_player_glory(self, membership_id):
        """
        Returns the current database Glory rating for a Player.
        """
        player_stats = self.db.session.query(models.Stats).join(models.Players).filter(models.Players.membership_id==str(membership_id)).order_by(models.Stats.timestamp.desc()).first()
        if player_stats:
            return player_stats.glory
        else:
            return

    def db_add_player_glory(self, membership_id, character_id, timestamp, new_glory):
        """
        Updates Glory rating for a Player. The only difference is the ability to pass in a Glory rating from somewhere else. TOOD: Wrap this and db_update_player_glory() into one function.
        """
        new_row = models.Stats(glory=new_glory, timestamp=timestamp)
        player = self.db.session.query(models.Players).filter(models.Players.membership_id==str(membership_id)).first()
        player.children_stats.append(new_row)
        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()

    def check_player_glory(self, membership_id, membership_type, character_id):
        """
        Compare the Player's current Glory rating to the latest Glory rating in the database. Updates the database value if the current glory rating is different.
        """
        current_glory_api = self.get_glory_ranking(membership_id, membership_type, character_id)
        if current_glory_api == 0:
            print('check_player_glory(): Current glory - 0.')
            current_glory_db = self.db.session.query(models.Stats.glory).join(models.Players).filter(models.Players.membership_id==membership_id).filter(models.Stats.glory != None).order_by(models.Stats.timestamp.desc()).first()
            if current_glory_db:
                print('check_player_glory(): Player went back down to 0 glory. Setting glory to 0.')
                glory_timestamp = datetime.now()
                self.db_add_player_glory(membership_id, character_id, glory_timestamp, current_glory_api)
            else:
                print('check_player_glory(): No action needed. DB value is also 0.')
        else:
            current_glory_db = self.db.session.query(models.Stats.glory).join(models.Players).filter(models.Players.membership_id==membership_id).filter(models.Stats.glory != None).order_by(models.Stats.timestamp.desc()).first()
            if current_glory_db:
                if current_glory_api != current_glory_db.glory:
                    print(f'check_player_glory(): Change in Glory detected. New - {current_glory_api} | Old - {current_glory_db.glory}')
                    glory_timestamp = datetime.now()
                    self.db_add_player_glory(membership_id, character_id, glory_timestamp, current_glory_api)
                else:
                    print('No change in glory')
            else:
                print(f'check_player_glory(): New glory entry: {current_glory_api}')
                glory_timestamp = datetime.now()
                self.db_add_player_glory(membership_id, character_id, glory_timestamp, current_glory_api)

    def db_get_player(self, player_name):
        player = self.db.session.query(models.Players).filter(models.Players.name==player_name).first()
        return player

    def db_get_player_by_id(self, membership_id):
        player = self.db.session.query(models.Players).filter(models.Players.membership_id==str(membership_id)).first()
        return player

    def get_characters(self, membership_id, membership_type):
        '''
        Returns a list of characterId strings for the provided membershipId.
        # Characters: 200 - This will get you summary info about each of the characters in the profile.
        '''
        character_list = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=200')
        if not character_list:
            return

        character_ids = [character for character in character_list['Response']['characters']['data']]
        return character_ids if character_ids else None

    def db_get_character_ids(self, player_id):
        """
        Retrieve a list of all character id's for a Player. Uses the database instead of the API.
        """
        characters = self.db.session.query(models.Characters).join(models.Players).filter(models.Players.membership_id==str(player_id)).all()
        return [char.char_id for char in characters]

    def db_get_characters(self, membership_id):
        """
        Retrieve all Characters from the database. Returns query objects.
        TODO: Change this to db_get_characters
        """
        characters = self.db.session.query(models.Characters).join(models.Players).filter(models.Players.membership_id==str(membership_id)).all()
        return characters

    def get_character_power(self, membership_id, character_id):
        character_stats = self.get_character(membership_id, character_id)
        power = character_stats['Response']['character']['data']['light']
        character = self.db.session.query(models.Characters).filter(models.Characters.char_id==str(character_id)).first()
        print(f'get_character_power(): updating power for character {character_id}. Old: {character.power} - New: {power}')
        character.power = power
        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()

    def get_characters_power(self, membership_id, profile):
        """Retrieve all power levels for each characters that a player has and store it in the db."""
        characters = self.db.session.query(models.Characters).join(models.Players).filter(models.Players.membership_id==membership_id).all()
        for char in characters:
            if char not in profile['Response']['characters']['data']:
                continue

            power = profile['Response']['characters']['data'][char.char_id]['light']
            if power > char.power:
                char.power = power
                try:
                    self.db.session.commit()
                except Exception as e:
                    self.db.session.rollback()
                    print(f'Failed to update power for character {char.char_id}. Reason: {e}')

    def get_activity_history(self, player, membership_type, char):
        activities = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Account/{player}/Character/{char}/Stats/Activities/')
        if activities:
            return activities
        else:
            return

    def get_pgcr(self, match_id):
        return utilities.http_get(f'https://stats.bungie.net/Platform/Destiny2/Stats/PostGameCarnageReport/{match_id}')

    def get_latest_pvp_activity_id(self, player, membership_type, char):
        """
        Retrieves the latest Crucible instanceId for a character.
        """
        activities = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Account/{player}/Character/{char}/Stats/Activities/?mode=5')
        if activities:
            if 'activities' in activities['Response']:
                return activities['Response']['activities'][0]['activityDetails']['instanceId']
            else:
                logger.warning(f'{player}:{membership_type}:{char}: Failed to retrieve latest pvp activity id due to activities not being in the response')
                return
        else:
            logger.warning(f'{player}:{membership_type}:{char}: Failed to retrieve latest pvp activity id due to failed http request')
            return

    def get_activity_history_by_mode(self, player, membership_type, char, mode, latest_pgcr):
        """Returns the entire crucible history for a character."""
        all_activities = []
        search = True
        page = 0
        pgcrs = None

        while search:
            try:
                logger.debug(f'{player}:{membership_type}:{char}:{mode} Fetching page {page}')
                activities = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Account/{player}/Character/{char}/Stats/Activities/?mode={mode}&page={page}&count=250')
            except Exception as e:
                logger.warning(f'{player}:{membership_type}:{char}:{mode} Failed to retrieve activities for mode')
                search = False

            if not activities:
                logger.warning(f'{player}:{membership_type}:{char}:{mode} Bad request. Activities returned null.')
                search = False
                return

            # If 1665 is returned, the profile is private and no further processing is necessary
            if activities == 1665:
                return

            # Empty Response key means the request is successful, but no activities were played
            if not activities['Response']:
                search = False

            if 'activities' in activities['Response']:
                pgcrs = [activity['activityDetails']['instanceId'] for activity in activities['Response']['activities'] if int(activity['activityDetails']['instanceId']) > int(latest_pgcr)]
                total_pgcrs = len(pgcrs)
                logger.debug(f'{player}:{membership_type}:{char}:{mode} Latest pgcr: {latest_pgcr} - New PGCRs found: {pgcrs} (Total: {total_pgcrs})')
                if total_pgcrs < 250:
                    logger.debug(f'{player}:{membership_type}:{char}:{mode} Latest PGCR found in response. Stopping search')
                    search = False

            if pgcrs:
                all_activities.extend(pgcrs)
                logger.debug(f'{player}:{membership_type}:{char}:{mode} Incrementing page')
                page = page + 1

        logger.debug(f'{player}:{membership_type}:{char}:{mode} PGCR Search stopped')
        if not all_activities:
            return

        # Activities should be in ascending order so they are processed oldest to newest
        all_activities = sorted(all_activities, key=lambda x: int(x))
        return all_activities

    def get_raid_stats(self):
        """
        We actually need to loop through all characters in each PGCR. If they're in the clan, continue processing. Skip if not.
        """
        start_time = datetime.now()
        raids = self.db.session.query(models.PostGameCarnageReport).filter(models.PostGameCarnageReport.mode==4).all()
        print(f'Get all raids query took: ', datetime.now() - start_time)
        clan_characters = [c.char_id for c in self.db.session.query(models.Characters).all()]

        for raid in raids:
            activity_hash = raid.data['Response']['activityDetails']['directorActivityHash']
            try:
                activity_name = self.get_definition('DestinyActivityDefinition', activity_hash)['displayProperties']['name']
            except Exception as e:
                logger.warning(f'Failed to get activity name for {activity_hash}')
                continue

            clan_members_in_raid = [c for c in raid.data['Response']['entries'] if c['characterId'] in clan_characters]

            for clan_member in clan_members_in_raid:
                character = self.db.session.query(models.Characters).filter(models.Characters.char_id==clan_member['characterId']).first()
                stats_exists = self.db.session.query(models.RaidStats).filter(models.RaidStats.pgcr_id==raid.pgcr_id).filter(models.RaidStats.parent_char==character.id).first()
                if stats_exists:
                    continue

                completion = int(clan_member['values']['completed']['basic']['value'])

                if completion < 1:
                    continue

                new_raid = models.RaidStats(
                    parent_char=character.id,
                    pgcr_id=raid.data['Response']['activityDetails']['instanceId'],
                    activity=activity_name,
                    activity_hash=activity_hash,
                    completed=completion,
                    duration=int(clan_member['values']['activityDurationSeconds']['basic']['value'])
                )

                self.db.session.add(new_raid)

                try:
                    self.db.session.commit()
                    now = datetime.now()
                except Exception as e:
                    logger.warning(f'Failed to commit db transaction. {e}')
                    self.db.session.rollback()

        print('Done. Time to run: ', datetime.now() - start_time)

    def get_raid_total(self):
        query = self.db.session.query(models.RaidStats.activity.label('raid'), func.count(models.RaidStats.id).label('total')).group_by(models.RaidStats.activity).order_by(func.count(models.RaidStats.id).desc()).all()

        for result in query:
            print(f'{result.raid}: {result.total}')

        return query

    def get_player_raids(self, name):
        all_raids = self.db.session.query(models.RaidStats.activity, func.count(models.RaidStats.activity).label('total')).join(models.Characters, models.Players).filter(models.Players.name==name).group_by(models.RaidStats.activity.label('raid')).all()
        for raid in all_raids:
            print(f'{raid.activity}: {raid.total}')

        total_count = self.db.session.query(models.RaidStats.id).join(models.Characters, models.Players).filter(models.Players.name==name).count()
        print(f'\nTotal raids: {total_count}')

    def get_forge_stats(self):
        query = self.db.session.query(models.Players.name.label('name'), func.count(models.PostGameCarnageReport.id).label('total')).join(models.Characters, models.Players.id==Characters.parent_id).filter(models.PostGameCarnageReport.parent_character==Characters.id).group_by(models.Players.name).order_by(func.count(models.PostGameCarnageReport.id).desc()).all()

        for result in query:
            print(f'{result.name}: {result.total}')

        return query

    def get_raid_totals(self):
        query = self.db.session.query(models.Players.name.label('name'), func.count(models.RaidStats.id).label('total')).join(models.Characters, models.Players.id==models.Characters.parent_id).filter(models.RaidStats.parent_char==models.Characters.id).group_by(models.Players.name).order_by(func.count(models.RaidStats.id).desc()).all()

        for result in query:
            print(f'{result.name}: {result.total}')

        return query

    def get_definition_inventory_item(self, item_hash):
        item = self.db.session.query(models.DestinyInventoryItemDefinition).filter(models.DestinyInventoryItemDefinition.hash==item_hash).first()
        if item:
            return item
        else:
            return

    def update_player_last_updated(self, membership_id):
        player = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        now = datetime.now()
        player.last_updated = now
        self.db.session.commit()

    def get_player_last_updated(self, membership_id):
        last_updated = self.db.session.query(models.Players.last_updated).filter(models.Players.membership_id==membership_id).first().last_updated
        last_updated_string = datetime.strftime(last_updated, '%Y-%m-%d %H:%M:%S')
        return last_updated_string

    def get_service_info(self):
        """Return the API version and the time of the last data refresh."""
        last_updated = self.db.session.query(models.Players).filter(models.Players.last_updated != None).order_by(models.Players.last_updated.desc()).first().last_updated
        last_updated = datetime.strftime(last_updated, '%Y-%m-%dT%H:%M:%SZ')
        return {
            "last_updated": last_updated,
            "api_version": "1.1"
        }

    def db_update_stats(self, membership_id, membership_type, online_status):
        """Update triumph, power, etc for a player. Used for the Clan Roster on the frontpage of the front-end."""
        try:
            profile = self.get_profile_all(membership_id, membership_type)
        except Exception as e:
            logger.info(f'Player {membership_id} ({membership_type} | Online: {online_status}) Failed to retrieve profile - {e}')
            return

        player = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        if not player:
            logger.debug(f'{membership_id}: player not found in database.')
            return

        # Update player's triumph score
        self.get_player_triumph(membership_id, profile, player)

        # Update the player's owned exotic collectibles
        self.get_profile_weapons(membership_id, profile)

        # Update the player's seals
        self.get_seals(membership_id, profile)

        # Get player's current title
        self.get_player_active_title(membership_id, profile)

        # TODO: Some profiles report more than one active currentActivityHash. Compare dateActivityStarted between the two and use the most recent one
        self.get_player_online_status(membership_id, profile, online_status, player)

        self.get_characters_power(membership_id, profile)
        self.db_update_player_last_played(membership_id, membership_type)
        self.update_player_last_updated(membership_id)

    def get_player_active_title(self, membership_id, profile):
        characters = profile['Response']['characters']['data']
        characters = sorted(characters, key=lambda k: characters[k]['dateLastPlayed'], reverse=True)
        active_title = None
        for character in characters:
            if 'titleRecordHash' in profile['Response']['characters']['data'][character]:
                title_hash = profile['Response']['characters']['data'][character]['titleRecordHash']
                gender_hash = str(profile['Response']['characters']['data'][character]['genderHash'])
                active_title = self.get_definition('DestinyRecordDefinition', title_hash)['titleInfo']['titlesByGenderHash'][gender_hash]
                break

        player = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        if not player:
            return

        if active_title:
            player.title = active_title
            try:
                self.db.session.commit()
            except Exception as e:
                logger.warning(f'{membership_id}: Failed to set active title to {active_title}')
                self.db.session.rollback()

    def get_player_triumph(self, membership_id, profile, player):
        """Update the player's triumph score in the database if the current value is higher than the previous value."""
        if 'data' in profile['Response']['profileRecords']:
            current_triumph = profile['Response']['profileRecords']['data']['score']

            if player.triumph:
                if current_triumph > player.triumph:
                    player.triumph = current_triumph
            else:
                player.triumph = current_triumph

            try:
                self.db.session.commit()
            except Exception as e:
                logger.warning(f'{membership_id}: Failed to update Triumph - {e}')
                self.db.session.rollback()

    def get_player_online_status(self, membership_id, profile, online_status, player):
        if online_status:
            if 'data' in profile['Response']['characterActivities']:
                current_activity = self.get_current_activity(profile['Response']['characterActivities']['data'])
                if current_activity:
                    now = datetime.utcnow()
                    activity_start_time = current_activity['dateActivityStarted']
                    activity_name = current_activity['currentActivityHash']
                    player.last_activity = activity_name
                    player.last_activity_time = activity_start_time
                    player.online = True
        else:
            now = datetime.utcnow()
            date_last_played = profile['Response']['profile']['data']['dateLastPlayed']
            player.last_activity_time = date_last_played
            player.online = False

        try:
            self.db.session.commit()
        except Exception as e:
            print(f'Player {membership_id} - Failed to commit activity information to database - {e}')
            self.db.session.rollback()

    # Section: DEFINITIONS - ACTIVITIES
    def get_definition_activity(self, activity_hash):
        """TODO: have to loop through all chars to get the current activity hash."""
        original_hash = activity_hash
        activity_hash = self.get_hash(activity_hash)
        if activity_hash == 82913930:
            return "Orbit"

        try:
            query = self.get_definition('DestinyActivityDefinition', original_hash)
            return query['displayProperties']['name']
        except Exception as e:
            print(f'Failed to get activity information for {activity_hash} (Original hash: {original_hash}).')
            return

    def get_definition_activity_mode(self, activity_mode_hash, character):
        """TODO: have to loop through all chars to get the current activity hash."""

        # Orbit doesn't have an ActivityMode hash, so just return
        if activity_mode_hash == 2166136261:
            return

        original_hash = activity_mode_hash
        activity_mode_hash = self.get_hash(activity_mode_hash)

        try:
            query = self.get_definition('DestinyActivityModeDefinition', activity_mode_hash, convert_hash=False)
            return query['displayProperties']['name']
        except Exception as e:
            logger.info(f'Character {character} - Failed to get ActivityMode information for {activity_mode_hash} (Original hash {original_hash})')
            return

    def get_current_activity(self, character_data):
        """current_activity = self.get_current_activity(profile['Response']['characterActivities']['data'])"""
        current_activities = []
        for k,v in character_data.items():

            # Character IDs are the only keys in the response that start with an integer, so meh
            if k[0].isdigit():
                current_character = k

            if v['currentActivityHash'] > 0:
                current_activity = self.get_definition_activity(v['currentActivityHash'])
                current_activity_mode = self.get_definition_activity_mode(v['currentActivityModeHash'], current_character)
                current_activity_date = character_data[k]['dateActivityStarted']
                current_activity = f'{current_activity_mode}: {current_activity}' if current_activity_mode else current_activity
                current_activities.append({'currentActivityHash': current_activity, 'dateActivityStarted': current_activity_date})
        
        if len(current_activities) > 1:
            return sorted(current_activities, key=lambda k: k['dateActivityStarted'], reverse=True)[0]
        elif current_activities:
            return current_activities[0]
        else:
            return

    def db_store_pgcr(self, player, character_id, match, mode):
        character = self.db.session.query(models.Characters).filter(models.Characters.char_id==character_id).first()
        pgcr = self.get_pgcr(match)
        if not pgcr:
            logger.warning(f'{match}: Failed to retrieve PGCR')
            return

        entry = models.PostGameCarnageReport(
            pgcr_id=pgcr['Response']['activityDetails']['instanceId'],
            data=pgcr,
            mode=mode,
            modes=pgcr['Response']['activityDetails']['modes'],
            date=pgcr['Response']['period'],
            parent_character=character.id
        )

        self.db.session.add(entry)

        try:
            self.db.session.commit()
            logger.info(f'{player}:{character_id}:{mode}:{match} PGCR successfully added to the database')
        except Exception as e:
            logger.warning(e)
            self.db.session.rollback()

    def db_update_match(self, char, match_id):
        match = self.get_pgcr(match_id)
        if not match:
            logger.warning(f'{match_id}:{mode} Failed to retrieve PGCR')
            return

        _entries = match['Response']['entries']
        matchtime = match['Response']['period']
        matchtime = matchtime.replace('T', ' ')[:-1]
        matchtime = datetime.strptime(matchtime, '%Y-%m-%d %H:%M:%S')
        #match_id = int(match['Response']['activityDetails']['instanceId'])
        #print(f'db_update_match(): Processing match {match_id}')
        char = str(char)
        _character = self.db.session.query(models.Characters).filter(models.Characters.char_id==char).first()
        player = self.db.session.query(models.Players).join(models.Characters).filter(models.Characters.char_id==char).first()

        for entry in _entries:
            # break this characterId if check so that it returns, remove it from the for loop
            if str(char) in entry['characterId']:
                if 'weapons' not in entry['extended']:
                    print('No weapons to process')
                    continue

                weapons = entry['extended']['weapons']
                for weapon in weapons:
                    kills = weapon['values']['uniqueWeaponKills']['basic']['displayValue']
                    kills = int(kills)

                    # Only proceed if the gun has kills. For some reason, some matches have reported guns without any actual kills associated with them
                    if kills <= 0:
                        print('Weapon has no kills. Continuing to next weapon.')
                        continue
                    
                    weap_ref_id = weapon['referenceId']
                    weapon_id = self.get_hash(weap_ref_id)

                    try:
                        _item = self.get_definition('DestinyInventoryItemDefinition', weapon_id, convert_hash=False)
                    except Exception as e:
                        print(f'Error processing {weapon_id}. Perhaps the Destiny DB needs an update? Skipping weapon.')
                        print(e)
                        continue

                    name = _item['displayProperties']['name']
                    item_bucket_hash = _item['inventory']['bucketTypeHash']
                    weapon_type = self.get_weapon_type(item_bucket_hash)
                    
                    if name != 'Classified':
                        subtype = _item['itemTypeDisplayName']
                    else:
                        subtype = 'Classified'

                    all_weapons = [weap.name for weap in self.db.session.query(models.Weapons).all()]
                    if name not in all_weapons:
                        # Add the weapon to our database if it does not exist
                        new = models.Weapons(name=name, damage_type=weapon_type, weapon_id=weapon_id, gun_type=subtype)
                        self.db.session.add(new)
                        self.db.session.commit()

                    _weap = self.db.session.query(models.Weapons).filter(models.Weapons.name==name).first()
                    new_weapon_entry = models.WeaponsData(kills=kills, match_time=matchtime, parent_id=_character.id, parent_weapon=_weap.id)
                    self.db.session.add(new_weapon_entry)

                    # TODO: maybe helper functions?
                    #   * add_weapon(<add a new weapons stats>)
                    #   * update_weapon(insert new weapond data)

        #print(f'{match_id}: match successfully processed')
        _character.last_pvp_match = str(match_id)

        # TODO: only update if there is new data - What was this referring to?
        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()

    # Section: CLASSIFIED WEAPON HANDLING
    def classified_weapon_check(self):
        classified_weapons = self.db.session.query(models.Weapons).filter(models.Weapons.name=='Classified').all()
        for weapon in classified_weapons:
            query = self.get_definition('DestinyInventoryItemDefinition', weapon.weapon_id)
            result_name = query['displayProperties']['name']
            if result_name != 'Classified':
                print(f'{result_name} ({weapon.weapon_id}) is no longer classified. Updating database.')
                weapon.name = result_name
                subtype = query['itemTypeDisplayName']
                weapon.gun_type = subtype
                self.db.session.commit()

    # Section: COLLECTIONS

    def get_collection_character(self, membership_id, character_id, presentation_node):
        """
        Retrieve collectibles from a specific presentation node from a character.
        """
        collection = utilities.http_get(f'https://bungie.net/Platform/Destiny2/4/Profile/{membership_id}/Character/{character_id}/Collectibles/{presentation_node}/?components=800')
        return collection

    def get_collection_char_weapons(self, membership_id, character_id):
        """
        Retrieve weapon collectibles from a character.
        """
        collection = utilities.http_get(f'https://bungie.net/Platform/Destiny2/4/Profile/{membership_id}/Character/{character_id}/Collectibles/2214408526/?components=800')
        return collection

    def get_collection_profile(self, membership_id, membership_type):
        """
        Retrieve a profile's collection.
        """
        collection = utilities.http_get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=800')

        if collection['ErrorCode'] != 1:
            print(f'Error retrieving collection for {membership_id}')
            return

        return collection

    def get_collection_profile_exotic_weapons(self, membership_id):
        PRESENTATION_NODE_WEAPON_HASHES = [3919988882, 2969886327, 1139971093]
        collection = self.get_collection_profile(membership_id)
        player = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()

        # Get profile-level collectibles
        for k,v in collection['Response']['profileCollectibles']['data']['collectibles'].items():
        
            if v['state'] != 0:
                continue

            collectible_definition = self.db_get_collectible_definition(k)

            if collectible_definition['presentationInfo']['presentationNodeType'] != 2:
                continue
            
            for node_hash in PRESENTATION_NODE_WEAPON_HASHES:
                if node_hash not in collectible_definition['presentationInfo']['parentPresentationNodeHashes']:
                    continue

                collectible_hash = str(collectible_definition['hash'])
                collectible_item_hash = str(collectible_definition['itemHash'])

    def get_collectible_exotic_weapons(self):
        """
        Updates our database with all exotic weapon collectibles from the Destiny database.
        """
        PRESENTATION_NODE_WEAPON_HASHES = [3919988882, 2969886327, 1139971093]
        PRESENTATION_NODE_TYPE_WEAPONS = 2
        COLLECTIBLE_KEY = {
            'Osiris': 1,
            'Warmind': 2,
            'Forsaken': 3,
            'Annual Pass': 4,
        }

        # '1642951315' = Wavesplitter (PS4 Exclusive)
        # '199171389' = Legend of Acrius (not sure why this shows up as not collected, might fix later)
        BANNED_WEAPONS = ['1642951315', '199171389']
        SEASON_OF_THE_DRIFTER_WEAPONS = ['Thorn', 'Arbalest', 'Outbreak Perfected']

        #exotic_weapon_collectibles = self.query_destiny_db_many('SELECT json FROM DestinyCollectibleDefinition')
        exotic_weapon_collectibles = self.get_definitions('DestinyCollectibleDefinition')
        for collectible in exotic_weapon_collectibles:
            data = collectible.json
            if data['redacted']:
                continue
            
            if data['presentationInfo']['presentationNodeType'] != PRESENTATION_NODE_TYPE_WEAPONS:
                continue

            for node_hash in PRESENTATION_NODE_WEAPON_HASHES:
                if node_hash not in data['presentationInfo']['parentPresentationNodeHashes']:
                    continue # Gets Exotic Kinetics

                collectible_hash = str(data['hash'])
                collectible_item_hash = str(data['itemHash'])
                collectible_name = data['displayProperties']['name']
                collectible_icon_url = data['displayProperties']['icon']
                required_version = data['stateInfo']['requirements']['entitlementUnavailableMessage']

                if collectible_hash in BANNED_WEAPONS:
                    continue

                '''
                Base game: 0
                Osiris = 1
                Warmind = 2
                Forsaken = 3
                Annual Pass / Black Armory = 4
                Season of the Drifter = 5
                Season of Opulence = 6 (but I manually set Opulence exotics to this ID in the db)
                '''

                if not required_version:
                    #print(f'{collectible_name}: {required_version}')
                    expansion = 0
                
                if 'Osiris' in required_version:
                    expansion = 1
                elif 'Warmind' in required_version:
                    expansion = 2
                elif 'Forsaken' in required_version:
                    expansion = 3
                elif 'Annual Pass' in required_version:
                    expansion = 4
                elif collectible_name in SEASON_OF_THE_DRIFTER_WEAPONS:
                    expansion = 5
                else:
                    if required_version:
                        expansion = -1
                        print(f'Expansion not found for {collectible_name} ({collectible_hash}) - required version {required_version}')
                        return

                '''
                #Code for fixing/updating expansion_id's on weapons that already exist in the db
                print(f'{collectible_name}: {expansion}')
                db_collectible = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.collectible_hash==collectible_hash).first()
                db_collectible.expansion_id = expansion
                self.db.session.commit()
                '''

                db_collectibles = self.db.session.query(models.CollectiblesGame).all()
                db_collectibles_list = [exotic.collectible_hash for exotic in db_collectibles]
                if collectible_hash not in db_collectibles_list:
                    print(f'New collectible: {collectible_name} ({collectible_hash})')
                    new_collectible = models.CollectiblesGame(collectible_hash=collectible_hash, name=collectible_name, item_hash=collectible_item_hash, presentation_node_type=str(PRESENTATION_NODE_TYPE_WEAPONS), parent_presentation_node_hash=str(node_hash), icon_url=collectible_icon_url, expansion_id=expansion)
                    self.db.session.add(new_collectible)
                    self.db.session.commit()

    def get_profile_weapons(self, membership_id, data):
        """
        Retrieve profile exotic weapon collectibles that are owned by a Player and store them in the database.
        """
        # Exotic Kinetic / Exotic Energy / Exotic Power
        PRESENTATION_NODE_WEAPON_HASHES = [3919988882, 2969886327, 1139971093]
        PRESENTATION_NODE_TYPE_WEAPONS = 2
        POLARIS_LANCE = '1642951318'
        UNCOLLECTED_STATES = [1, 3, 8, 11, 17, 19]
        BANNED_WEAPONS = ['1642951315', '199171389']

        player = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        if not player:
            logger.warning(f'{membership_id}: failed to update collectibles. Player not found in database.')
            return

        if 'data' not in data['Response']['profileCollectibles']:
            logger.debug(f'{membership_id}: profileCollectibles is private. Skipping profileColletible check.')
            return

        # Profile-level collectibles
        for k,v in data['Response']['profileCollectibles']['data']['collectibles'].items():

            # Skip the collectible if we do not own it. If this result is odd, we do not own the collectible
            if v['state'] % 2 != 0:
                continue

            collectible_definition = self.get_definition('DestinyCollectibleDefinition', k)
            if not collectible_definition:
                logger.warning(f'{membership_id} - DestinyCollectibleDefinition {k}: Failed to retrieve definition')
                continue

            if collectible_definition['redacted']:
                #Convert to logging.info print(f'Redacted collectible definition: {k}')
                logger.warning(f'{membership_id} - DestinyCollectibleDefinition {k}: Redacted definition')
                continue

            # Skip non-Weapon items
            if collectible_definition['presentationInfo']['presentationNodeType'] != PRESENTATION_NODE_TYPE_WEAPONS:
                continue

            for node_hash in PRESENTATION_NODE_WEAPON_HASHES:
                if node_hash not in collectible_definition['presentationInfo']['parentPresentationNodeHashes']:
                    continue # Gets Exotic Kinetics

                collectible_hash = str(collectible_definition['hash'])
                collectible_item_hash = str(collectible_definition['itemHash'])
                collectible_name = collectible_definition['displayProperties']['name']

                if collectible_hash in BANNED_WEAPONS:
                    continue

                player_collectibles = self.db.session.query(models.CollectiblesGame).join(models.CollectiblesPlayer).join(models.Players).filter(models.Players.membership_id==membership_id).all()
                player_collectibles_list = [_collectible.collectible_hash for _collectible in player_collectibles]
                if collectible_hash not in player_collectibles_list:
                    parent = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.collectible_hash==collectible_hash).first()
                    if not parent:
                        print(f'Collectible {collectible_hash}: No parent to attach to. Skipping. P.S. update the DB!')
                        continue

                    print(f'New collectible for {player.name}: {collectible_name}')
                    new_collectible = models.CollectiblesPlayer(parent_player=player.id, date_collected=datetime.now())
                    parent.child_collectible.append(new_collectible)
                    try:
                        self.db.session.commit()
                    except Exception as e:
                        self.db.session.rollback()
                        print(f'Error adding new collectible {collectible_name} for {player.name}')

        # Character-level collectibles
        if 'data' not in data['Response']['characterCollectibles']:
            logger.info(f'{membership_id}: characterCollectibles is private. Skipping characterColletible check.')
            return

        characters = [character for character in data['Response']['characterCollectibles']['data']]

        for character in characters:
            # By checking for the collectible on every character, we can skips the remaining unprocessed characters if its found on the 1st character
            player_collectibles = self.db.session.query(models.CollectiblesGame).join(models.CollectiblesPlayer).join(models.Players).filter(models.Players.membership_id==membership_id).all()
            player_collectibles_list = [_collectible.collectible_hash for _collectible in player_collectibles]
            if POLARIS_LANCE in player_collectibles_list:
                continue

            for k,v in data['Response']['characterCollectibles']['data'][str(character)]['collectibles'].items():
                if k == POLARIS_LANCE:
                    if v['state'] % 2 != 0:
                        print(f'New collectible for {player.name}: Polaris Lance')
                        new_collectible = models.CollectiblesPlayer(parent_player=player.id, date_collected=datetime.now())
                        parent = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.collectible_hash==POLARIS_LANCE).first()
                        parent.child_collectible.append(new_collectible)
                        self.db.session.commit()


    def get_collection_profile_weapons(self, membership_id, membership_type):
        """
        Retrieve exotic weapon collectibles that are owned by a Player and store them in the database.
        """
        # Exotic Kinetic / Exotic Energy / Exotic Power
        PRESENTATION_NODE_WEAPON_HASHES = [3919988882, 2969886327, 1139971093]
        PRESENTATION_NODE_TYPE_WEAPONS = 2
        POLARIS_LANCE = '1642951318'
        UNCOLLECTED_STATES = [1, 3, 8, 11, 17, 19]
        BANNED_WEAPONS = ['1642951315', '199171389']

        collection = self.get_collection_profile(membership_id, membership_type)
        player = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()

        if not collection:
            print(f'Error retrieving collectibles. Skipping {membership_id}')
            return

        # Profile-level collectibles
        for k,v in collection['Response']['profileCollectibles']['data']['collectibles'].items():

            # Skip the collectible if we do not own it. If this result is odd, we do not own the collectible
            if v['state'] % 2 != 0:
                continue
            
            collectible_definition = self.db_get_collectible_definition(k)

            # Skip non-Weapon items
            if collectible_definition['presentationInfo']['presentationNodeType'] != PRESENTATION_NODE_TYPE_WEAPONS:
                continue

            for node_hash in PRESENTATION_NODE_WEAPON_HASHES:
                if node_hash not in collectible_definition['presentationInfo']['parentPresentationNodeHashes']:
                    continue # Gets Exotic Kinetics

                collectible_hash = str(collectible_definition['hash'])
                collectible_item_hash = str(collectible_definition['itemHash'])
                collectible_name = collectible_definition['displayProperties']['name']

                if collectible_hash in BANNED_WEAPONS:
                    continue

                player_collectibles = self.db.session.query(models.CollectiblesGame).join(models.CollectiblesPlayer).join(models.Players).filter(models.Players.membership_id==membership_id).all()
                player_collectibles_list = [_collectible.collectible_hash for _collectible in player_collectibles]
                if collectible_hash not in player_collectibles_list:
                    parent = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.collectible_hash==collectible_hash).first()
                    if not parent:
                        print(f'Collectible {collectible_hash}: No parent to attach to. Skipping.')
                        continue

                    print(f'New collectible for {player.name}: {collectible_name}')
                    now = datetime.now()
                    new_collectible = models.CollectiblesPlayer(parent_player=player.id, date_collected=now)
                    parent.child_collectible.append(new_collectible)
                    self.db.session.commit()

        # Character-level collectibles
        characters = [character for character in collection['Response']['characterCollectibles']['data']]

        for character in characters:
            #print(f'Checking {character}')

            # By checking for the collectible on every character, we can skips the remaining unprocessed characters if its found on the 1st character
            player_collectibles = self.db.session.query(models.CollectiblesGame).join(models.CollectiblesPlayer).join(models.Players).filter(models.Players.membership_id==membership_id).all()
            player_collectibles_list = [_collectible.collectible_hash for _collectible in player_collectibles]
            if POLARIS_LANCE in player_collectibles_list:
                continue

            for k,v in collection['Response']['characterCollectibles']['data'][str(character)]['collectibles'].items():
                if k == POLARIS_LANCE:
                    if v['state'] % 2 != 0:
                        print(f'New collectible for {player.name}: Polaris Lance')
                        now = datetime.now()
                        new_collectible = models.CollectiblesPlayer(parent_player=player.id, date_collected=now)
                        parent = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.collectible_hash==POLARIS_LANCE).first()
                        parent.child_collectible.append(new_collectible)
                        self.db.session.commit()

    def db_get_collection_exotic_weapons_unowned(self):
        players = [player.id for player in self.db.session.query(models.Players).all()]
        unowned_exotics = self.db.session.query(models.CollectiblesGame).filter(~models.CollectiblesGame.child_collectible.any(models.CollectiblesPlayer.parent_player.in_(players))).all()
        return unowned_exotics

    def api_get_collectible_exotics_unowned(self):
        players = [player.id for player in self.db.session.query(models.Players).all()]
        unowned_exotics = self.db.session.query(models.CollectiblesGame).filter(~models.CollectiblesGame.child_collectible.any(models.CollectiblesPlayer.parent_player.in_(players))).order_by(models.CollectiblesGame.expansion_id.desc()).all()
        results = self.collectibles_schema.dump(unowned_exotics)
        return jsonify(results.data)

    def db_get_collection_exotic_weapons_owned(self):
        players = [player.id for player in self.db.session.query(models.Players).all()]
        owned_exotics = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.child_collectible.any(models.CollectiblesPlayer.parent_player.in_(players))).all()
        all_data = []        
        for exotic in owned_exotics:
            owners = self.db_get_collectible_exotic_weapon_owners(exotic.collectible_hash)
            owners_list = [owner.name for owner in owners]
            all_data.append(DestinyWeaponOwners(weapon=exotic, owners=owners_list))

        return all_data

    def api_get_collectible_exotics_owned(self):
        players = [player.id for player in self.db.session.query(models.Players).all()]
        owned_exotics = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.child_collectible.any(models.CollectiblesPlayer.parent_player.in_(players))).order_by(models.CollectiblesGame.expansion_id.desc()).all()
        all_data = []        
        for exotic in owned_exotics:
            owners = self.db_get_collectible_exotic_weapon_owners(exotic.collectible_hash)
            owners_list = [owner.name for owner in owners]
            dwo = DestinyWeaponOwners(weapon=exotic, owners=owners_list).serialize()
            all_data.append(dwo)

        return all_data

    def db_get_collectible(self, collectible_hash):
        collectible = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.collectible_hash==collectible_hash).first()
        if not collectible:
            return

        owners = self.db_get_collectible_exotic_weapon_owners(collectible_hash)
        owners_list = [owner.name for owner in owners]
        obj = DestinyWeaponOwners(weapon=collectible, owners=owners_list)
        return obj.serialize()

    def db_exotic_owners(self):
        players = [player.id for player in self.db.session.query(models.Players).all()]
        exotics = self.db.session.query(models.CollectiblesGame, models.Players).join(models.CollectiblesPlayer).join(models.Players).group_by(models.CollectiblesGame.id, models.Players.id).filter(models.CollectiblesGame.child_collectible.any(models.CollectiblesPlayer.parent_player != None)).all()
        return exotics

    def db_reset_collectibles(self):
        """
        Deletes all Collectible information from the database.
        """
        self.db.session.query(models.CollectiblesPlayer).delete()
        self.db.session.commit()
        self.db.session.query(models.CollectiblesGame).delete()
        self.db.session.commit()
        print('All Collectible data has been deleted from the database.')

    def get_character_collectibles_weapons(self, membership_id, character_id):
        player_collection = self.get_collection_char_weapons(membership_id, character_id)
        owned_collectible_ids = []
        unowned_collectible_ids = []
        owned_collectibles = []
        unowned_collectibles = []
        all_weapons = self.db_get_all_weapons()
        for k,v in player_collection['Response']['collectibles']['data']['collectibles'].items():
            if v['state'] == 0:
                owned_collectible_ids.append(k)
            else:
                unowned_collectible_ids.append(k)

        print('\nOwned exotic weapons:')
        for collectible in owned_collectible_ids:
            collectible_definition = self.db_get_collectible_definition(collectible)
            owned_collectibles.append(collectible_definition['displayProperties']['name'])

        print('\nUnowned exotic weapons:')
        for collectible in unowned_collectible_ids:
            collectible_definition = self.db_get_collectible_definition(collectible)
            unowned_collectibles.append(collectible_definition['displayProperties']['name'])

        return owned_collectibles, unowned_collectibles

    def db_get_collectible_definition(self, _hash):
        """
        Retrieves the JSON for a Collectible definition.
        """
        collectible_hash = self.get_hash(_hash)
        query = self.query_destiny_db(f'SELECT json FROM DestinyCollectibleDefinition WHERE id = {collectible_hash}')
        return query

    def db_get_collectible_exotic_weapon_owners(self, collectible_hash):
        """
        Returns the owners of an exotic weapon collectible.
        """
        owners = self.db.session.query(models.Players).join(models.CollectiblesPlayer).join(models.CollectiblesGame).filter(models.CollectiblesGame.collectible_hash==collectible_hash).all()
        return owners

    def db_get_collectible_exotic_weapons_for_player(self, membership_id):
        """
        Retrieves all exotic weapon collectibles owned by a player.
        """
        owned_exotics = self.db.session.query(models.CollectiblesGame).join(models.CollectiblesPlayer).join(models.Players).filter(models.Players.membership_id==membership_id).all()
        return owned_exotics

    def db_get_collectible_exotic_weapons_for_player_unowned(self, membership_id):
        player_id = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        unowned_exotics = self.db.session.query(models.CollectiblesGame).filter(~models.CollectiblesGame.child_collectible.any(models.CollectiblesPlayer.parent_player==player_id.id)).all()
        return unowned_exotics

    def db_get_collectible_exotic_weapons_for_player_owned(self, membership_id):
        player_id = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        owned_exotics = self.db.session.query(models.CollectiblesGame).filter(models.CollectiblesGame.child_collectible.any(models.CollectiblesPlayer.parent_player==player_id.id)).all()
        return owned_exotics

    def db_get_collectible_exotic_weapons_per_player(self):
        """
        Returns the number of exotics owned per player.
        """
        exotics_owned_count = self.db.session.query(models.Players.name, func.count(models.CollectiblesPlayer.id)).group_by(models.Players.name).filter(models.CollectiblesPlayer.parent_player==Players.id).order_by(func.count(models.CollectiblesPlayer.id).desc()).all()
        return exotics_owned_count

    def get_player_profile_collectibles(self, membership_id):
        player_collection = self.get_collection_profile(membership_id)
        collectible_list = []
        owned_collectibles = []
        all_weapons = self.db_get_all_weapons()
        for collectible in player_collection['Response']['profileCollectibles']['data']['collectibles']:
            collectible_list.append(collectible)

        for collectible in collectible_list:
            collectible_hash = self.get_hash(collectible)
            collectible_definition = self.query_destiny_db(f'SELECT json FROM DestinyCollectibleDefinition WHERE id = {collectible_hash}')
            owned_collectibles.append(collectible_definition['displayProperties']['name'])
    
        return owned_collectibles

    def db_get_all_weapons(self):
        """
        Retrieves a list of all weapons from the Destiny 2 database.
        """
        weapon_bucket_hashes = [1498876634, -1829672231, 953998645]
        weapon_tier_hashes = [-286569176, -1535467725]
        all_weapons = self.query_destiny_db_many('SELECT json FROM DestinyInventoryItemDefinition')
        all_weapons_list = []
        for weapon in all_weapons:
            data = json.loads(weapon[0])
            bucket_hash = self.get_hash(data['inventory']['bucketTypeHash'])
            tier_hash = self.get_hash(data['inventory']['tierTypeHash'])
            if bucket_hash in weapon_bucket_hashes:
                if tier_hash in weapon_tier_hashes:
                    name = data['displayProperties']['name']
                    all_weapons_list.append(name)

        return all_weapons_list

    def get_weapon_type(self, _hash):
        weapon_type = self.get_definition('DestinyInventoryBucketDefinition', _hash)
        weapon_type_name = weapon_type['displayProperties']['name']
        weapon_type_name = weapon_type_name.lower()
        weapon_type_name = weapon_type_name.split(' ')[0]
        return weapon_type_name

    def get_player_top_weapon(self, membership_id):
        weapons = self.get_player_weapons(membership_id)
        top_weapon = weapons[0].name
        return top_weapon

    def get_player_top_weapon_days(self, membership_id, days):
        weapons = self.get_player_weapons_days(membership_id, days)
        if weapons:
            top_weapon = weapons[0].name
            return top_weapon
        else:
            return

    def get_player(self, membership_id):
        return self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()

    def api_get_player(self, membership_id):
        player = self.db.session.query(models.Players.name, models.Players.membership_id, models.Players.last_activity, models.Players.last_activity_time, models.Players.triumph, models.Players.title, models.Players.seals, models.Players.join_date, models.Players.online, func.max(models.Characters.power).label("highest_power")) \
            .join(models.Characters) \
            .group_by(models.Players.name, models.Players.membership_id, models.Players.last_activity, models.Players.last_activity_time, models.Players.seals, models.Players.join_date, models.Players.online, models.Players.triumph, models.Players.title) \
            .filter(models.Players.membership_id==membership_id) \
            .order_by(func.max(models.Characters.power).label("highest_power").desc()) \
            .first()

        return DestinyPlayer(player=player).serialize()

    def get_player_characters_power(self, player_name):
        return self.db.session.query(models.Characters).join(models.Players).filter(models.Players.name==player_name).order_by(models.Characters.power.desc()).all()

    def get_player_by_id(self, membership_id):
        query = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        print(query.name)
        return query

    def api_get_char_kills(self, membership_id, days):
        """Returns a Player's Crucible weapon kill count for each character class."""
        if days == 0:
            query = self.db.session.query(models.Characters.class_name, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .join(models.Players) \
                .group_by(models.Characters.class_name) \
                .filter(models.Players.membership_id==membership_id) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            results = self.character_schema.dump(query)
            return jsonify(results.data)
        elif days > 0:
            time_range = datetime.now() - timedelta(days=days)
            query = self.db.session.query(models.Characters.class_name, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .join(models.Players) \
                .group_by(models.Characters.class_name) \
                .filter(models.Players.membership_id==membership_id) \
                .filter(models.WeaponsData.match_time >= time_range) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            results = self.character_schema.dump(query)
            return jsonify(results.data)

    def get_player_characters_kills(self, player_name, days):
        if days == 0:
            return self.db.session.query(models.Characters.class_name, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .join(models.Players) \
                .group_by(models.Characters.class_name) \
                .filter(models.Players.name==player_name) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
        elif days > 0:
            time_range = datetime.now() - timedelta(days=days)
            return self.db.session.query(models.Characters.class_name, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .join(models.Players) \
                .group_by(models.Characters.class_name) \
                .filter(models.Players.name==player_name) \
                .filter(models.WeaponsData.match_time >= time_range) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()

    def get_player_character_id(self, player_id):
        character_id = self.db.session.query(models.Characters).join(models.Players).filter(models.Players.membership_id==str(player_id)).first()
        if character_id:
            return character_id.char_id
        else:
            return

    def get_player_weapons(self, membership_id):
        weapons = self.db.session.query(models.Weapons.name, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
            .join(models.WeaponsData) \
            .join(models.Characters) \
            .join(models.Players) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id) \
            .filter(models.Players.membership_id==membership_id) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        return weapons

    def api_get_player_weapons(self, membership_id, days):
        """Returns all weapon kill counts for a Player."""
        if days == 0:
            weapons = self.db.session.query(models.Weapons.name, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .join(models.Characters) \
                .join(models.Players) \
                .group_by(models.Weapons.name, models.Weapons.weapon_id) \
                .filter(models.Players.membership_id==membership_id) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            results = self.player_weapon_schema.dump(weapons)
            return jsonify(results.data)
        elif days > 0:
            time_range = datetime.now() - timedelta(days=days)
            weapons = self.db.session.query(models.Weapons.name, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .join(models.Characters) \
                .join(models.Players) \
                .group_by(models.Weapons.name, models.Weapons.weapon_id) \
                .filter(models.Players.membership_id==membership_id) \
                .filter(models.WeaponsData.match_time >= time_range) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            results = self.player_weapon_schema.dump(weapons)
            return jsonify(results.data)

    def get_player_weapons_days(self, membership_id, days):
        if days == 0:
            weapons = self.db.session.query(models.Weapons.name, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.WeaponsData) \
                .join(models.Characters) \
                .join(models.Players) \
                .group_by(models.Weapons.name, models.Weapons.weapon_id) \
                .filter(models.Players.membership_id==membership_id) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            return weapons

        month = datetime.now() - timedelta(days=days)
        weapons = self.db.session.query(models.Weapons.name, models.Weapons.weapon_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
            .join(models.WeaponsData) \
            .join(models.Characters) \
            .join(models.Players) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id) \
            .filter(models.Players.membership_id==membership_id) \
            .filter(models.WeaponsData.match_time >= month) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        return weapons

    def get_top_weapon_by_type(self, weapon_type):
        if weapon_type not in self.WEAPON_TYPES:
            print('Invalid weapon type. Valid weapon types: kinetic, energy, power')
            return

        results = self.db.session.query(models.Weapons.name, func.sum(models.WeaponsData.kills).label("total_kills"), models.Weapons.weapon_id) \
            .join(models.WeaponsData) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id) \
            .filter(models.Weapons.damage_type==weapon_type) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        return results

    def get_top_weapon_by_type_days(self, weapon_type, days):
        if weapon_type not in self.WEAPON_TYPES:
            print('Invalid weapon type. Valid weapon types: kinetic, energy, power')
            return

        if days == 0:
            results = self.db.session.query(models.Weapons.name, func.sum(models.WeaponsData.kills).label("total_kills"), models.Weapons.weapon_id) \
                .join(models.WeaponsData) \
                .group_by(models.Weapons.name, models.Weapons.weapon_id) \
                .filter(models.Weapons.damage_type==weapon_type) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            return results

        timerange = datetime.now() - timedelta(days=days)
        results = self.db.session.query(models.Weapons.name, func.sum(models.WeaponsData.kills).label("total_kills"), models.Weapons.weapon_id) \
            .join(models.WeaponsData) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id) \
            .filter(models.Weapons.damage_type==weapon_type) \
            .filter(models.WeaponsData.match_time >= timerange) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        return results

    def api_get_all_weapons(self, days):
        if days == 0:
            results = self.db.session.query(models.Weapons.name, func.sum(models.WeaponsData.kills).label("total_kills"), models.Weapons.weapon_id) \
                .join(models.WeaponsData) \
                .group_by(models.Weapons.name, models.Weapons.weapon_id) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            results = self.weapon_type_kills_schema.dump(results)
            return jsonify(results.data)

        timerange = datetime.now() - timedelta(days=days)
        results = self.db.session.query(models.Weapons.name, func.sum(models.WeaponsData.kills).label("total_kills"), models.Weapons.weapon_id) \
            .join(models.WeaponsData) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id) \
            .filter(models.WeaponsData.match_time >= timerange) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        results = self.weapon_type_kills_schema.dump(results)
        return jsonify(results.data)

    def api_get_top_weapon_by_type(self, weapon_type, days):
        if weapon_type not in self.WEAPON_TYPES:
            print('Invalid weapon type. Valid weapon types: kinetic, energy, power')
            return

        if days == 0:
            results = self.db.session.query(models.Weapons.name, func.sum(models.WeaponsData.kills).label("total_kills"), models.Weapons.weapon_id) \
                .join(models.WeaponsData) \
                .group_by(models.Weapons.name, models.Weapons.weapon_id) \
                .filter(models.Weapons.damage_type==weapon_type) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            results = self.weapon_type_kills_schema.dump(results)
            return jsonify(results.data)

        timerange = datetime.now() - timedelta(days=days)
        results = self.db.session.query(models.Weapons.name, func.sum(models.WeaponsData.kills).label("total_kills"), models.Weapons.weapon_id) \
            .join(models.WeaponsData) \
            .group_by(models.Weapons.name, models.Weapons.weapon_id) \
            .filter(models.Weapons.damage_type==weapon_type) \
            .filter(models.WeaponsData.match_time >= timerange) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        results = self.weapon_type_kills_schema.dump(results)
        return jsonify(results.data)

    def get_weapon_name(self, weapon_id):
        name = self.db.session.query(models.Weapons.name).filter(models.Weapons.weapon_id==weapon_id).first()
        if name:
            return name.name
        else:
            return

    def api_get_weapon(self, weapon_id):
        """Return the name, gun type, and id for a Weapon."""
        query = self.db.session.query(models.Weapons).filter(models.Weapons.weapon_id==weapon_id).first()
        if not query:
            return

        results = self.weapon_schema.dump(query)
        return jsonify(results.data)

    def api_get_weapon_kills(self, weapon_id, days):
        """
        Returns kills (within X days) by every Player for a specific Weapon during a specified time range.
        """
        weapon = self.get_definition_inventory_item(weapon_id)
        if not weapon:
            return

        total_kills = func.sum(models.WeaponsData.kills).label('total_kills')
        if days == 0:
            weapon_stats = self.db.session.query(models.Players.name, models.Players.membership_id, total_kills) \
                .select_from(models.Characters) \
                .join(models.WeaponsData, models.Players) \
                .group_by(models.Players.name, models.Players.membership_id) \
                .filter(models.Weapons.weapon_id==weapon_id) \
                .order_by(total_kills.desc()) \
                .all()
            results = self.weapon_kills_schema.dump(weapon_stats)
            return jsonify(results.data)

        time_range = datetime.now() - timedelta(days=days)
        weapon_stats = self.db.session.query(models.Players.name, models.Players.membership_id, total_kills) \
            .select_from(models.Characters) \
            .join(models.WeaponsData, models.Players) \
            .group_by(models.Players.name, models.Players.membership_id) \
            .filter(models.Weapons.weapon_id==weapon_id) \
            .filter(models.WeaponsData.match_time >= time_range) \
            .order_by(total_kills.desc()) \
            .all()

        results = self.weapon_kills_schema.dump(weapon_stats)
        return jsonify(results.data)

    def get_weapon_kills_days(self, weapon_id, days):
        """
        Returns all kills (within X days) by every Player for a specific Weapon.
        """
        if days == 0:
            weapon_stats = self.db.session.query(models.Players.name, models.Players.membership_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
                .join(models.Characters) \
                .join(models.WeaponsData) \
                .join(models.Weapons) \
                .group_by(models.Players.name, models.Players.membership_id) \
                .filter(models.Weapons.weapon_id==weapon_id) \
                .order_by(func.sum(models.WeaponsData.kills).desc()) \
                .all()
            return weapon_stats

        time_range = datetime.now() - timedelta(days=days)
        weapon_stats = self.db.session.query(models.Players.name, models.Players.membership_id, func.sum(models.WeaponsData.kills).label('total_kills')) \
            .join(models.Characters) \
            .join(models.WeaponsData) \
            .join(models.Weapons) \
            .group_by(models.Players.name, models.Players.membership_id) \
            .filter(models.Weapons.weapon_id==weapon_id) \
            .filter(models.WeaponsData.match_time >= time_range) \
            .order_by(func.sum(models.WeaponsData.kills).desc()) \
            .all()
        return weapon_stats

    def db_reset_crucible_data(self):
        """
        TODO: Move to its own file, like 'utils' or 'admin_functions'
        Effectively wipes out all match related data for all characters. Resets each characters' last match played value, and wipes out all entries in models.WeaponsData.
        """
        self.db.session.query(models.WeaponsData).delete()
        all_chars = self.db.session.query(models.Characters).all()
        for char in all_chars:
            char.last_pvp_match = 0

        try:
            self.db.session.commit()
            print('Set all characters last_pvp_match to 0')
            print('Deleted all entires in models.WeaponsData')
        except Exception as e:
            self.db.session.rollback()

    def get_character_last_activity_by_mode(self, membership_id, character, mode):
        latest_pgcr = self.db.session.query(models.PostGameCarnageReport).join(models.Characters).filter(models.Characters.char_id==character.char_id).filter(models.PostGameCarnageReport.mode==mode).order_by(models.PostGameCarnageReport.date.desc()).first()
        latest_activity_id = latest_pgcr.pgcr_id if latest_pgcr else '0'
        logger.debug(f'{membership_id}:{character.char_id}:{mode} Latest activity id: {latest_activity_id}')
        return latest_activity_id

    def get_new_matches(self, membership_id, membership_type, mode):
        """
        Called from /app/workers/pgcr_collector.py
        Retrieves new PGCR IDs for new Crucible matches played by all characters for each clan member,
        and sends them to Redis for processing by a consumer.
        Returns a list of new matches played. Returns nothing if there are no matches played.
        """
        clan_member = self.db.session.query(models.Players).filter(models.Players.membership_id==membership_id).first()
        if not clan_member:
            logger.debug(f'{membership_id}: Player not found in database')
            return

        # Construct the base dictionary that we will send back to Redis
        redis_data = {
            'membershipId': clan_member.membership_id,
            'membershipType': clan_member.membership_type,
            'characters': [],
            'mode': mode
        }

        characters = self.db_get_characters(clan_member.membership_id)
        if not characters:
            return

        for character in characters:
            latest_match = self.get_character_last_activity_by_mode(membership_id, character, mode)

            try:
                matches = self.get_activity_history_by_mode(membership_id, membership_type, character.char_id, mode, latest_match)
            except Exception as e:
                logger.warning(f'{membership_id}:{membership_type}:{character.char_id}:{mode} Failed to get new matches. Reason: {e}')
                continue

            if not matches:
                continue

            redis_data['characters'].append({'characterId': character.char_id, 'mode': mode, 'matches': matches})
            logger.debug(f'{membership_id}:{membership_type}:{character.char_id}:{mode} Sending data to consumer: {redis_data}')

        return redis_data

class DestinyWeaponOwners(object):
    """This is mainly for serializing a Destiny Weapon object. I needed a way to return a list of players that own a particular weapon to the front-end via the API."""
    def __init__(self, weapon, owners):
        self.weapon = weapon
        self.owners = owners

    def get_hash(self, _hash):
        _hash = int(_hash)
        if (_hash & (1 << (32 - 1))) != 0:
            _hash = _hash - (1 << 32)
        return _hash

    def serialize(self):
        item_hash = self.get_hash(self.weapon.item_hash)
        return {
            'name': self.weapon.name,
            'icon_url': self.weapon.icon_url,
            'item_hash': str(item_hash),
            'collectible_hash': self.weapon.collectible_hash,
            'owners': [owner for owner in self.owners]
        }

class DestinyPlayer(object):
    """This is mainly for serializing a Destiny Player object. I needed a way to return a list of seals to the front-end via the API."""
    def __init__(self, player):
        self.player = player

    def serialize(self):
        last_activity_time = datetime.strftime(self.player.last_activity_time, '%Y-%m-%dT%H:%M:%SZ') if self.player.last_activity_time else None
        join_date_time = datetime.strftime(self.player.join_date, '%Y-%m-%dT%H:%M:%SZ') if self.player.join_date else None
        return {
            'name': self.player.name,
            'membership_id': self.player.membership_id,
            'triumph': self.player.triumph,
            'last_activity': self.player.last_activity,
            'last_activity_time': last_activity_time,
            'join_date': join_date_time,
            'highest_power': self.player.highest_power,
            'seals': [seal for seal in self.player.seals.split(',')] if self.player.seals else [],
            'online': self.player.online,
            'title': self.player.title
        }
