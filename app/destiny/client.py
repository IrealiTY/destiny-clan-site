import os
from time import sleep
from datetime import datetime, timedelta
from pathlib import Path
import inspect
import json
import zipfile
import shutil
import sqlite3
import re
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from flask import jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, relationship
from app.models import db, Players, Characters, Weapons, WeaponsData, Stats, Manifest, CollectiblesGame, CollectiblesPlayer, PlayerSchema, PlayersSchema, PlayerWeaponSchema, CharacterSchema, WeaponKillsSchema, WeaponSchema, CollectibleSchema, WeaponTypeKillsSchema, WeaponCategoryKillsSchema
from app import create_app
from config import Config, ConfigProd
import logging

#logging.basicConfig(level=logging.DEBUG)

class DestinyAPI(object):
    def __init__(self):
        self.api_key = Config.BUNGIE_API_KEY
        if os.environ.get('CLANENV') == 'prod':
            print('DestinyAPI: Loaded prod db')
            self.database = ConfigProd.db_url
        else:
            print('DestinyAPI: Loaded dev db')
            self.database = Config.db_url_dev

        self.WEAPON_TYPES = ['all', 'kinetic', 'energy', 'power']
        self.SUPERUSERS_ID = 2823954
        self.SWAMPFOX_ID = 198175
        self.CLAN_ID = self.SWAMPFOX_ID
        self.BUNGIE_BASE_URL = 'https://www.bungie.net'
        self.db = db

        self.players_schema = PlayersSchema(many=True)
        self.player_schema = PlayerSchema()
        self.player_weapon_schema = PlayerWeaponSchema(many=True)
        self.character_schema = CharacterSchema(many=True)
        self.weapon_kills_schema = WeaponKillsSchema(many=True)
        self.weapon_type_kills_schema = WeaponTypeKillsSchema(many=True)
        self.weapon_schema = WeaponSchema()
        self.collectible_schema = CollectibleSchema()
        self.collectibles_schema = CollectibleSchema(many=True)
        self.weapon_category_kills_schema = WeaponCategoryKillsSchema(many=True)

    # Section: Utilities (HTTP, files, printing, JSON, etc)
    def requests_retry_session(self, retries=3, backoff_factor=1, status_forcelist=(500, 502, 503, 504), session=None):
        session = session or requests.Session()
        retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update(self.api_key)
        return session
    
    def _get(self, url):
        try:
            request = self.requests_retry_session().get(url)
        except Exception as e:
            print('_get error: ', e)
            return

        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = "Error - " + str(e)
            print(error)
            return error

        data = json.loads(request.text)
        if data['ErrorCode'] != 1:
            self.print_json(data)
            return data
        return data

    def save_file(self, _data, _filename, path=False):
        _filename = str(_filename)
        """
        Save JSON data to a file.
        """
        if path:
            file_name = _filename + ".json"
            file_path = path / file_name
            #print(file_path.absolute())
            with file_path.open('w', encoding='utf-8') as outfile:
                json.dump(_data, outfile, indent=4, sort_keys=True)
                full_path = file_path.absolute().as_posix()
                print(f'Data saved to file: {full_path}')
        else:
            with open(f'{_filename}.json', 'w') as outfile:
                json.dump(_data, outfile, indent=4, sort_keys=True)
                print(f'Data saved to file: {_filename}.json')

    def print_json(self, resp):
        print(json.dumps(resp, indent=4))

    def get_hash(self, _hash):
        _hash = int(_hash)
        if (_hash & (1 << (32 - 1))) != 0:
            _hash = _hash - (1 << 32)
        return _hash

    # Section: API - Buckets
    def get_bucket(self, bucket_hash):
        bucket_hash = self.get_hash(bucket_hash)
        bucket = self.query_destiny_db(f'SELECT json FROM DestinyInventoryBucketDefinition WHERE id = {bucket_hash}')
        return bucket

    # Section API - Historical stats
    def get_historical_stats_account(self, membership_id):
        """
        Returns aggregate historical stats for an account in two forms: per character, and merged (all character aggregate historical stats merged).
        Documentation: https://bungie-net.github.io/multi/operation_get_Destiny2-GetHistoricalStatsForAccount.html#operation_get_Destiny2-GetHistoricalStatsForAccount
        """
        stats = self._get(f'https://www.bungie.net/Platform/Destiny2/4/Account/{membership_id}/Stats/')
        return stats

    # Section: Manifest
    def get_manifest(self):
        """
        Returns the current Destiny 2 API manifest.
        Documentation: https://bungie-net.github.io/multi/operation_get_Destiny2-GetDestinyManifest.html#operation_get_Destiny2-GetDestinyManifest
        """
        manifest = self._get('https://www.bungie.net/Platform/Destiny2/Manifest/')
        return manifest

    def get_manifest_url(self):
        """
        Returns the URL for the current Destiny 2 SQLITE database file.
        How to use: https://github.com/vpzed/Destiny2-API-Info/wiki/API-Introduction-Part-3-Manifest
        """
        manifest = self.get_manifest()
        manifest_db_name = manifest['Response']['mobileWorldContentPaths']['en']
        new_db_url = f'{self.BUNGIE_BASE_URL}{manifest_db_name}'
        return new_db_url

    def db_check_manifest_url(self):
        """
        Checks the current manifest database URL from the API against the manifest database URL that we last downloaded.
        Returns false if the URL has not changed. Returns true if it has changed.
        """
        new_url = self.get_manifest_url()
        current_manifest = self.db.session.query(Manifest).first()
        if not current_manifest:
            date_updated = datetime.now()
            new_manifest_url = Manifest(url=new_url, updated=date_updated)
            self.db.session.add(new_manifest_url)
        else:
            if current_manifest.url == new_url:
                print('Manifest URL has not changed. Stopping.')
                return False

            print('New manifest found.')
            current_manifest.url = new_url
            current_manifest.updated = datetime.now()

        try:
            self.db.session.commit()
            print('Manifest url successfully updated in the database.')
        except Exception as e:
            self.db.session.rollback()
            print('Manifest URL was not updated in the database.')

        return True

    def get_new_manifest(self, force=False):
        """
        Downloads the new content database and overwrites the old one.
        """
        if not force:
            if not self.db_check_manifest_url():
                print('No new manifest to download.')
                return
        else:
            print('Forcing update')

        print('Downloading new content database.')
        manifest_url = self.get_manifest_url()
        r = requests.get(manifest_url, headers=self.api_key, stream=True)
        with open('newdb.zip', 'wb') as f:
            for chunk in r.iter_content():
                f.write(chunk)

        print('New db downloaded to: newdb.zip')
        with zipfile.ZipFile('newdb.zip', 'r') as zip_ref:
            zip_ref.extractall('.')

        print('Extracting newdb.zip')

        files_in_dir = [f for f in os.listdir('.')]
        for f in files_in_dir:
            if '.content' in f:
                db_file = f

        print(f'DB extracted to {db_file}')
        current_directory = os.getcwd()
        src = os.path.join(current_directory, db_file)
        dst = os.path.join(current_directory, 'db.sqlite3')
        shutil.move(src, dst)
        
        print(f'{db_file} has been moved to db.sqlite3')

        file_to_delete = os.path.join(current_directory, 'newdb.zip')
        if os.path.isfile(file_to_delete):
            os.remove(file_to_delete)
            print('Deleted newdb.zip')

        # Todo add a test to verify it works, if it fails, roll back to other db (todo: copy old db to "db.sqlite3.old" before deleting)

    def get_profile(self, membership_id, membership_type):
        profile = self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=100')
        return profile

    def get_profile_all(self, membership_id, membership_type):
        profile = self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=100,700,900,200,204,800')
        return profile

    def get_profile2(self, membership_id):
        profile = self._get(f'https://www.bungie.net/Platform/Destiny2/4/Profile/{membership_id}/?components=100,200,204,900')
        return profile

    def get_profile_records(self, membership_id, membership_type):
        profile = self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=900')
        return profile

    def get_profile_presentation_nodes(self, membership_id, membership_type):
        profile = self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=700')
        return profile

    def get_presentation_node_definition(self, presentation_node):
        query = self.query_destiny_db(f'SELECT json FROM DestinyPresentationNodeDefinition WHERE id = {presentation_node}')
        return query

    def get_record_definition(self, record):
        query = self.query_destiny_db(f'SELECT json FROM DestinyRecordDefinition WHERE id = {record}')
        return query

    # SECTION: PRESENTATION NODES / SEALS
    def get_seals(self, membership_id, profile):

        obtained_seals = []

        # Get the root presentation node for Seals
        query = self.query_destiny_db('SELECT json FROM DestinyPresentationNodeDefinition WHERE id = 1652422747')

        # Get a list of presentation nodes for each seal
        seal_presentation_nodes = [str(node['presentationNodeHash']) for node in query['children']['presentationNodes']]
        
        for node in seal_presentation_nodes:
            if node in profile['Response']['profilePresentationNodes']['data']['nodes']:

                # Current progress of the objective
                node_progress = profile['Response']['profilePresentationNodes']['data']['nodes'][node]['progressValue']

                # Required progress for the objective (if it's 6, then progressValue needs to be 6 for this to be completed)
                node_progress_completed = profile['Response']['profilePresentationNodes']['data']['nodes'][node]['completionValue']

                # Get the presentation node definition for the seal
                seal_presentation_node = self.get_presentation_node_definition(int(self.get_hash(node)))
                if seal_presentation_node['redacted']:
                    #print(f'{node} is redacted')
                    continue

                # Get the record definition for the seal
                seal_completion_record_hash = self.get_hash(int(seal_presentation_node['completionRecordHash']))

                # Get the title rewarded by the seal
                title = self.get_record_definition(seal_completion_record_hash)['titleInfo']['titlesByGender']['Male']

                #print(f'{node}: {node_progress} / {node_progress_completed} ({title})')

                if node_progress == node_progress_completed:
                    obtained_seals.append(title)
            else:
                unbroken_hash = '2039028930'
                characters = [k for k,v in profile['Response']['characterPresentationNodes']['data'].items()]
                for character in characters:
                    node_progress = profile['Response']['characterPresentationNodes']['data'][character]['nodes'][unbroken_hash]['progressValue']
                    node_progress_completed = profile['Response']['characterPresentationNodes']['data'][character]['nodes'][unbroken_hash]['completionValue']
                    unbroken_presentation_node = self.get_presentation_node_definition(int(unbroken_hash))
                    unbroken_completion_record_hash = self.get_hash(int(unbroken_presentation_node['completionRecordHash']))
                    title = self.get_record_definition(unbroken_completion_record_hash)['titleInfo']['titlesByGender']['Male']
                    #print(f'{node}: {node_progress} / {node_progress_completed} ({title})')
                    if node_progress == node_progress_completed:
                        obtained_seals.append(title)
                        break

        if obtained_seals:
            player = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()
            if not player:
                return

            player.seals = ','.join(obtained_seals)
            try:
                self.db.session.commit()
            except Exception as e:
                self.db.session.rollback()

    def player_update_triumph(self, membership_id, membership_type):
        try:
            records = self.get_profile_records(membership_id, membership_type)
        except:
            print(f'Error retrieving records for {membership_id}')
            return

        if records['ErrorCode'] != 1:
            print(f'Error retrieving account for {membership_id}')
            return

        player = self.db_get_player_by_id(membership_id)
        new_triumph = records['Response']['profileRecords']['data']['score']

        if player.triumph:
            if new_triumph > player.triumph:
                player.triumph = new_triumph
                print(f'New triumph score for {player.name} ({player.membership_id}): {new_triumph}')
        else:
            player.triumph = new_triumph

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

    def db_update_players_last_played(self):
        clan_members = self.db_get_clan_member_ids()
        for clan_member in clan_members:
            last_played_time = self.get_player_last_played(clan_member)
            player = self.db.session.query(Players).filter(Players.membership_id==clan_member).first()
            print(f'Setting last_played time for {clan_member} to {last_played_time}')
            player.last_played = last_played_time
            self.db.session.commit()

    def db_update_player_last_played(self, membership_id, membership_type):
        """Updates the database with the time that the player last played from the API."""
        player = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()
        player.last_played = self.get_player_last_played_obj(membership_id, membership_type)
        self.db.session.commit()

    def get_display_name(self, membership_id):
        profile = self._get(f'https://www.bungie.net/Platform/Destiny2/4/Profile/{membership_id}/?components=100')
        return profile['Response']['profile']['data']['userInfo']['displayName']

    def get_all_player_kills(self):
        kills = self.db.session.query(Players.name, Players.membership_id, Players.last_played, func.sum(WeaponsData.kills).label("total_kills")) \
            .join(Characters) \
            .join(WeaponsData) \
            .group_by(Players.name, Players.membership_id) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        return kills

    def get_all_player_kills_range(self, days):
        date_range = datetime.now() - timedelta(days=days)
        kills = self.db.session.query(Players.name, Players.membership_id, func.sum(WeaponsData.kills).label("total_kills")) \
            .join(Characters) \
            .join(WeaponsData) \
            .group_by(Players.name, Players.membership_id) \
            .filter(WeaponsData.match_time >= date_range) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        return kills

    def get_top_weapon_by_subtype(self, subtype, page):
        weapon_type_results = self.db.session.query(Weapons.name, Weapons.gun_type, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
            .join(WeaponsData) \
            .group_by(Weapons.name, Weapons.weapon_id, Weapons.gun_type) \
            .filter(Weapons.gun_type==subtype) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .paginate(page, 10, False)
        return weapon_type_results

    def get_top_weapon_by_subtype_days(self, subtype, page, days):
        if days == 0:
            weapon_type_results = self.db.session.query(Weapons.name, Weapons.gun_type, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .group_by(Weapons.name, Weapons.weapon_id, Weapons.gun_type) \
                .filter(Weapons.gun_type==subtype) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .paginate(page, 10, False)
            return weapon_type_results

        time_range = datetime.now() - timedelta(days=days)
        weapon_type_results = self.db.session.query(Weapons.name, Weapons.gun_type, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
            .join(WeaponsData) \
            .group_by(Weapons.name, Weapons.weapon_id, Weapons.gun_type) \
            .filter(Weapons.gun_type==subtype) \
            .filter(WeaponsData.match_time >= time_range) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .paginate(page, 10, False)
        return weapon_type_results

    def api_get_weapon_category_kills(self, category, days):
        if days == 0:
            query = self.db.session.query(Weapons.name, Weapons.gun_type, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .group_by(Weapons.name, Weapons.weapon_id, Weapons.gun_type) \
                .filter(Weapons.gun_type==category) \
                .order_by(func.sum(WeaponsData.kills).desc())

            results = self.weapon_category_kills_schema.dump(query)
            return jsonify(results.data)

        time_range = datetime.now() - timedelta(days=days)
        query = self.db.session.query(Weapons.name, Weapons.gun_type, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
            .join(WeaponsData) \
            .group_by(Weapons.name, Weapons.weapon_id, Weapons.gun_type) \
            .filter(Weapons.gun_type==category) \
            .filter(WeaponsData.match_time >= time_range) \
            .order_by(func.sum(WeaponsData.kills).desc())

        results = self.weapon_category_kills_schema.dump(query)
        return jsonify(results.data)
    
    def get_player_kills(self, membership_id, days):
        if days > 0:
            time_range = datetime.now() - timedelta(days=days)
            return self.db.session.query(Players.name, func.sum(WeaponsData.kills).label("total_kills")) \
                .join(Characters) \
                .join(WeaponsData) \
                .group_by(Players.name) \
                .filter(Players.membership_id==membership_id) \
                .filter(WeaponsData.match_time >= time_range) \
                .first()
        else:
            return self.db.session.query(Players.name, func.sum(WeaponsData.kills).label("total_kills")) \
                .join(Characters) \
                .join(WeaponsData) \
                .group_by(Players.name) \
                .filter(Players.membership_id==membership_id) \
                .first()

    def get_total_clan_kills(self):
        return self.db.session.query(func.sum(WeaponsData.kills).label('total_kills')).first()

    def get_character(self, membership_id, membership_type, character_id):
        """Retrieve a character from the API."""
        return self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/Character/{character_id}/?components=200')

    def get_player_vs_char_played_time(self, membership_id):
        characters = self.db_get_character_ids(membership_id)
        for character in characters:
            class_name = self.db.session.query(Characters).filter(Characters.char_id==character).first().class_name
            character_last_played = self.get_character(membership_id, character)['Response']['character']['data']['dateLastPlayed']
            print(f'{class_name} - last played: {character_last_played}')

        player_last_played = self.get_player_last_played(membership_id)
        player_name = self.db.session.query(Players).filter(Players.membership_id==f'{membership_id}').first().name
        print(f'{player_name} - last played: {player_last_played}')

    def query_destiny_db(self, query):
        connection = sqlite3.connect('db.sqlite3')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        for r in row:
            data = json.loads(r)
        connection.close()
        return data

    def query_destiny_db_many(self, query):
        connection = sqlite3.connect('db.sqlite3')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        connection.close()
        return rows

    def db_get_total_weapons(self):
        '''
        Returns a count of the total number of weapons used in the Crucible by clan members.
        '''
        weapon_count = self.db.session.query(func.count(Weapons.id)).first()[0]
        return weapon_count

    # SECTION: Clan member management
    def db_get_total_characters(self):
        '''
        Returns a count of the total number of clan characters.
        '''
        character_count = self.db.session.query(func.count(Characters.id)).first()[0]
        return character_count

    def db_get_total_clan_members(self):
        '''
        Returns a count of the total number of clan members.
        '''
        clan_member_count = self.db.session.query(func.count(Players.id)).first()[0]
        return clan_member_count

    def get_clan_member_ids(self, clan_id):
        '''
        Returns a list of membership_id's from the API for all the characters in the provided clan id.
        '''
        clan_id = self.CLAN_ID
        clan = self._get(f'https://www.bungie.net/Platform/GroupV2/{clan_id}/Members/')
        return [clan_member['destinyUserInfo']['membershipId'] for clan_member in clan['Response']['results']]

    def db_get_clan_member_ids(self):
        """
        Returns a list of membership_id's from our DB for all clan members.
        """
        ids = [clan_member.membership_id for clan_member in self.db.session.query(Players).all()]
        return ids

    def db_get_clan_members(self):
        """
        Returns a list of all clan member query objects from the database.
        """
        return [player for player in self.db.session.query(Players).all()]

    def get_clan_members_api(self):
        clan = self._get(f'https://www.bungie.net/Platform/GroupV2/{self.CLAN_ID}/Members/')
        clan_members = []
        for member in clan['Response']['results']:
            '''
            player = self.db.session.query(Players).filter(Players.membership_id==member['destinyUserInfo']['membershipId']).first()
            lastOnlineStatusChange = int(member['lastOnlineStatusChange'])
            if lastOnlineStatusChange > 0:
                last_played = datetime.fromtimestamp(lastOnlineStatusChange)
            else:
                continue

            if player.last_activity_time:
                if last_played > player.last_activity_time:
                    clan_members.append(
                        {
                            'membershipId': member['destinyUserInfo']['membershipId'],
                            'membershipType': member['destinyUserInfo']['membershipType'],
                            'isOnline': member['isOnline']
                        })
            else:
                clan_members.append(
                    {
                        'membershipId': member['destinyUserInfo']['membershipId'],
                        'membershipType': member['destinyUserInfo']['membershipType'],
                        'isOnline': member['isOnline']
                    })
            '''
            clan_members.append(
                {
                    'membershipId': member['destinyUserInfo']['membershipId'],
                    'membershipType': member['destinyUserInfo']['membershipType'],
                    'isOnline': member['isOnline']
                })

        return clan_members

    '''
    API
    '''
    def get_clan_members(self):
        """
        7/2/2019 Delete
        """
        players = self.db.session.query(Players.name, Players.membership_id, Players.last_played, Players.triumph, func.sum(WeaponsData.kills).label("total_kills")) \
            .join(Characters) \
            .join(WeaponsData) \
            .group_by(Players.name, Players.membership_id, Players.last_played, Players.triumph) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        players = self.players_schema.dump(players)
        return jsonify(players.data)

    def api_get_roster(self):
        all_players = []
        players = self.db.session.query(Players.name, Players.membership_id, Players.last_activity, Players.last_activity_time, Players.triumph, Players.seals, Players.online, func.max(Characters.power).label("highest_power")) \
            .join(Characters) \
            .group_by(Players.name, Players.membership_id, Players.last_activity, Players.last_activity_time, Players.triumph, Players.seals, Players.online) \
            .order_by(func.max(Characters.power).label("highest_power").desc()) \
            .all()

        for player in players:
            data = DestinyPlayer(player=player).serialize()
            all_players.append(data)

        return all_players
        #players = self.players_schema.dump(players)
        #return jsonify(players.data)

    # Should this be our 'check if all current clan members from the API match the current clan members in the DB' function? If so, rename it.
    def get_former_clan_members(self):
        """
        Returns a list of clan members that exist in the database but are no longer in the clan (via API).
        """
        current_members_api = self.get_clan_member_ids(self.CLAN_ID)
        current_members_db = self.db_get_clan_member_ids()
        former_members = list(set(current_members_db).difference(current_members_api))
        if former_members:
            for member in former_members:
                name = self.db.session.query(Players).filter(Players.membership_id==member).first().name
                print(f'{member} - {name}')
            return former_members
        else:
            print('There are no members to delete.')
            return

    def db_remove_former_clan_members(self):
        members_to_delete = self.get_former_clan_members()
        if not members_to_delete:
            print('No members to delete.')
            return
        
        for member in members_to_delete:
            print(f'Deleting player {member}')
            chars_to_delete = [char.id for char in self.db.session.query(Characters).join(Players).filter(Players.membership_id==member).all()]

            # Delete all weapons for every character
            for char in chars_to_delete:
                self.db.session.query(WeaponsData).filter(WeaponsData.parent_id==char).delete()
                self.db.session.commit()

            # Delete all characters that the Player has
            for char in chars_to_delete:
                self.db.session.query(Characters).filter(Characters.id==char).delete()
                self.db.session.commit()

            player_id = self.db.session.query(Players).filter(Players.membership_id==member).first().id

            # Delete collectibles associated with the player
            self.db.session.query(CollectiblesPlayer).filter(CollectiblesPlayer.parent_player==player_id).delete()
            self.db.session.commit()
            sleep(0.5)

            # Delete stats associated with the player
            self.db.session.query(Stats).filter(Stats.parent_player==player_id).delete()
            self.db.session.commit()
            sleep(0.5)

            # Delete Player
            self.db.session.query(Players).filter(Players.membership_id==member).delete()
            self.db.session.commit()

    # Section: CRUCIBLE - GLORY
    def get_glory_ranking(self, membership_id, membership_type, character_id):
        """
        Returns the current Glory rating for a Player.
        """
        character_progression = self._get(f'https://bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/Character/{character_id}/?components=202')
        if character_progression['ErrorStatus'] == 'SystemDisabled':
            print('API is under maintenance. Current glory has not been returned.')
            return False

        glory = character_progression['Response']['progressions']['data']['progressions']['2679551909']['currentProgress']
        return glory

    def db_get_player_glory(self, membership_id):
        """
        Returns the current database Glory rating for a Player.
        """
        player_stats = self.db.session.query(Stats).join(Players).filter(Players.membership_id==str(membership_id)).order_by(Stats.timestamp.desc()).first()
        if player_stats:
            return player_stats.glory
        else:
            return

    def db_add_player_glory(self, membership_id, character_id, timestamp, new_glory):
        """
        Updates Glory rating for a Player. The only difference is the ability to pass in a Glory rating from somewhere else. TOOD: Wrap this and db_update_player_glory() into one function.
        """
        new_row = Stats(glory=new_glory, timestamp=timestamp)
        player = self.db.session.query(Players).filter(Players.membership_id==str(membership_id)).first()
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
            current_glory_db = self.db.session.query(Stats.glory).join(Players).filter(Players.membership_id==membership_id).filter(Stats.glory != None).order_by(Stats.timestamp.desc()).first()
            if current_glory_db:
                print('check_player_glory(): Player went back down to 0 glory. Setting glory to 0.')
                glory_timestamp = datetime.now()
                self.db_add_player_glory(membership_id, character_id, glory_timestamp, current_glory_api)
            else:
                print('check_player_glory(): No action needed. DB value is also 0.')
        else:
            current_glory_db = self.db.session.query(Stats.glory).join(Players).filter(Players.membership_id==membership_id).filter(Stats.glory != None).order_by(Stats.timestamp.desc()).first()
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

    def get_glory_progress_lunas(self, membership_id):
        """
        Returns the progress (as a percentage) of a Player's journey to 2100 Glory.
        """
        glory = self.db_get_player_glory(membership_id)
        glory_percentage = "{:.0%}".format(int(glory)/2100)
        return glory_percentage

    # Section: CLAN - CHARACTERS

    def db_update_clan_members(self, clan_id):
        """
        Fetch the current clan roster from the API and store the new members in the database.
        """
        clan = self._get(f'https://www.bungie.net/Platform/GroupV2/{clan_id}/Members/')
        for clan_member in clan['Response']['results']:
            player_name = clan_member['destinyUserInfo']['displayName']
            player_id = str(clan_member['destinyUserInfo']['membershipId'])
            platform = clan_member['destinyUserInfo']['membershipType']
            date_joined = clan_member['joinDate']
            player_check = self.db.session.query(Players).filter(Players.membership_id==player_id).first()
            if not player_check:
                print(f'New player: {player_name} ({player_id})')
                new = Players(name=player_name, membership_id=player_id, membership_type=platform, join_date=date_joined)
                self.db.session.add(new)
                self.db.session.commit()
            else:
                if not player_check.membership_type:
                    print(f'Updating platform for {player_name}: {platform}')
                    player_check.membership_type = platform
                    try:
                        self.db.session.commit()
                    except Exception as e:
                        self.db.session.rollback()

                if not player_check.join_date:
                    print(f'Updating join date for {player_name}: {date_joined}')
                    player_check.join_date = date_joined
                    try:
                        self.db.session.commit()
                    except Exception as e:
                        self.db.session.rollback()

    def db_get_player(self, player_name):
        player = self.db.session.query(Players).filter(Players.name==player_name).first()
        return player

    def db_get_player_by_id(self, membership_id):
        player = self.db.session.query(Players).filter(Players.membership_id==str(membership_id)).first()
        return player

    def get_characters(self, membership_id, membership_type):
        '''
        Returns a list of characterId strings for the provided membershipId.
        # Characters: 200 - This will get you summary info about each of the characters in the profile.
        '''
        character_list = self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=200')
        if not character_list:
            print(f'get_characters(): error fetching charaters for {membership_id} with membershipType {membership_type}')
            return

        if character_list['ErrorCode'] > 1:
            print('Error retrieving characters.')
            print(character_list['Message'])
            return
            
        character_ids = [character for character in character_list['Response']['characters']['data']]
        return character_ids

    def db_get_character_ids(self, player_id):
        """
        Retrieve a list of all character id's for a Player. Uses the database instead of the API.
        """
        characters = self.db.session.query(Characters).join(Players).filter(Players.membership_id==str(player_id)).all()
        return [char.char_id for char in characters]

    def db_get_characters(self, membership_id):
        """
        Retrieve all Characters from the database. Returns query objects.
        TODO: Change this to db_get_characters
        """
        characters = self.db.session.query(Characters).join(Players).filter(Players.membership_id==str(membership_id)).all()
        return characters

    def util_get_chars(self, player_name):
        characters = self.db.session.query(Characters).join(Players).filter(Players.name==player_name).all()
        membership_id = self.db.session.query(Players).filter(Players.name==player_name).first().membership_id
        print(f'Characters for {player_name} ({membership_id})')
        for character in characters:
            print(f'{character.class_name} ({character.char_id}) - Last pvp match: {character.last_pvp_match}')

    def db_update_characters(self):
        '''
        Updates the database with all characters in the clan.
        Queries the API to: get all clan members -> get all characters for each member -> stores in db
        Each row for a character has a reference back to its Player.
        '''
        if not self.db_is_alive():
            return

        player_ids = self.db_get_clan_member_ids()
        for player in player_ids:
            # TODO: Technically this would be bad if someone was to delete a char and recreate it but whatever
            player_chars_in_db = [char.char_id for char in self.db.session.query(Characters).join(Players).filter(Players.membership_id==player).all()]
            if len(player_chars_in_db) == 3:
                continue

            # We need to fetch the db object so that we can .append to it later in the function
            _player = self.db.session.query(Players).filter(Players.membership_id==f'{player}').first()
            _id = int(_player.membership_id)
            player_chars = self.get_characters(_id, _player.membership_type)
            if not player_chars:
                print('No chars returned. Skipping.')
                continue
            
            if len(player_chars_in_db) == len(player_chars):
                continue

            for char in player_chars:
                if char not in player_chars_in_db:
                    print(f'{_player.name} ({_player.membership_id}): Adding new character {char}')
                    _character = self.get_character(_id, _player.membership_type, char)
                    _power = _character['Response']['character']['data']['light']
                    class_hash = _character['Response']['character']['data']['classHash']
                    class_id = self.get_hash(class_hash)
                    _class_name = self.query_destiny_db(f'SELECT json FROM DestinyClassDefinition WHERE id = {class_id}')
                    char_class = _class_name['displayProperties']['name']
                    new = Characters(char_id=char, class_name=char_class, power=_power, last_pvp_match=0)
                    _player.children.append(new)

        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()

    def get_character_power(self, membership_id, character_id):
        character_stats = self.get_character(membership_id, character_id)
        power = character_stats['Response']['character']['data']['light']
        character = self.db.session.query(Characters).filter(Characters.char_id==str(character_id)).first()
        print(f'get_character_power(): updating power for character {character_id}. Old: {character.power} - New: {power}')
        character.power = power
        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()

    def get_characters_power(self, membership_id, profile):
        """Retrieve all power levels for each characters that a player has and store it in the db."""
        characters = self.db.session.query(Characters).join(Players).filter(Players.membership_id==membership_id).all()
        for char in characters:
            power = profile['Response']['characters']['data'][char.char_id]['light']
            if power > char.power:
                char.power = power
                try:
                    self.db.session.commit()
                except Exception as e:
                    self.db.session.rollback()
                    print(f'Failed to update power for character {char.char_id}. Reason: {e}')

    def get_activity_history(self, player, membership_type, char):
        return self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{player}/Character/{char}/Stats/Activities/')

    def get_pgcr(self, match_id):
        match = self._get(f'https://stats.bungie.net/Platform/Destiny2/Stats/PostGameCarnageReport/{match_id}')
        return match

    def get_latest_pvp_activity_id(self, player, membership_type, char):
        """
        Retrieves the latest Crucible instanceId for a character.
        """
        activities = self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{player}/Character/{char}/Stats/Activities/?mode=5')
        if activities['Response']:
            latest_activity_id = activities['Response']['activities'][0]['activityDetails']['instanceId']
            return latest_activity_id
        else:
            return

    def get_crucible_history(self, player, membership_type, char):
        """
        Returns the entire crucible history for a character.
        TODO: https://bonar-jira.bonar.lab/browse/CLAN-83
        """
        max_pages = 10
        calls = 0
        all_activities = []
        for p in range(max_pages):
            activities = self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{player}/Character/{char}/Stats/Activities/?mode=5&page={p}&count=250')
            #sleep(0.2)
            calls = calls + 1
            
            if 'activities' in activities['Response']:
                for activity in activities['Response']['activities']:
                    instance_id = activity['activityDetails']['instanceId']
                    all_activities.append(instance_id)
            else:
                #print('No results. Stopping.') # Don't really need this anymore, it was only for testing to see if we can properly stop when there's no results left to page
                break

        all_activities = list(reversed(all_activities))
        print(f'Calls: {calls}')
        return all_activities

    def get_weapon(self, weapon_id):
        item = self.query_destiny_db(f'SELECT json FROM DestinyInventoryItemDefinition WHERE id = {weapon_id}')
        return item['displayProperties']['name']

    def update_player_last_updated(self, membership_id):
        player = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()
        now = datetime.now()
        player.last_updated = now
        self.db.session.commit()

    def get_player_last_updated(self, membership_id):
        last_updated = self.db.session.query(Players.last_updated).filter(Players.membership_id==membership_id).first().last_updated
        last_updated_string = datetime.strftime(last_updated, '%Y-%m-%d %H:%M:%S')
        return last_updated_string

    def db_get_all_clan_stats(self, force=False, nosave=False):
        """
        Update crucible match data for all Players (and their characters) in the clan.
        """
        start_time = datetime.now()

        # get players, then get their characters, then get their crucible matches, then get their stats
        clan_members = self.db_get_clan_members()
        for member in clan_members:

            # https://jira.bonar.lab/browse/CLAN-101
            self.get_collection_profile_weapons(member.membership_id, member.membership_type)
            api_calls = 1

            player = self.db.session.query(Players).filter(Players.membership_id==member.membership_id).first()
            member_last_played_db = player.last_played
            member_last_played_api_string = self.get_player_last_played(member.membership_id, member.membership_type)
            api_calls = api_calls + 1

            if not member_last_played_api_string:
                print(f'Error retrieving profile information for {member.membership_id}. Skipping.')
                continue

            member_last_played_api = datetime.strptime(member_last_played_api_string, '%Y-%m-%dT%H:%M:%SZ')

            if not force:
                if member_last_played_api == member_last_played_db:
                    print(f'Player {player.name} ({member.membership_id}) has not played recently. Skipping.')
                    continue

            # TODO: make this return a list of character objects for the player, that way we don't have to do 3 queries a few lines down after 'for char in chars'
            chars = self.db_get_character_ids(member.membership_id)
            if not chars:
                print(f'No characters found for {member.membership_id}. Skipping player.')
                continue

            for char in chars:

                # https://jira.bonar.lab/browse/CLAN-104
                self.check_player_glory(member.membership_id, member.membership_type, char)
                api_calls = api_calls + 1

                _character = self.db.session.query(Characters).filter(Characters.char_id==char).first()
                print(f'\n-------------\ndb_get_all_clan_stats(): Processing matches for Player: {player.name} ({member.membership_id}) - Character: {_character.char_id} - Last match: {_character.last_pvp_match} - Last played (db): {player.last_played} - Last played (API): {member_last_played_api_string}')

                # TODO: Is this necessary?
                # Required to skip characters that have an empty activity history
                acts = self.get_activity_history(member.membership_id, member.membership_type, char) # API call count - 1
                api_calls = api_calls + 1
                # If most recent match here matches char.last_pvp_match - we can probably continue the loop?
                if not isinstance(acts, dict):
                    #print(f'Error: failed to retrieve activities. Skipping character. {_player} - {char}')
                    continue

                # TODO: for every recent activity, create a list of instance id's that are greater than last_pvp_match
                if 'activities' not in acts['Response']:
                    #print('db_get_all_clan_stats(): Character has no recent activities. Skipping.')
                    continue

                # If the latest Crucible activity id played by the character matches the character's last_pvp_match database value, skip
                latest_crucible_match = self.get_latest_pvp_activity_id(member.membership_id, member.membership_type, char)
                api_calls = api_calls + 1
                if latest_crucible_match:
                    if _character.last_pvp_match == latest_crucible_match:
                        print(f'db_get_all_clan_stats(): No new crucible matches played since the last one. Skipping character.')
                        continue

                matches_to_process = []
                matches = self.get_crucible_history(member.membership_id, member.membership_type, char) # API call count - 2
                if not isinstance(acts, dict):
                    print(f'Error: failed to retrieve activities. Skipping character (player: {member.membership_id} - char: {char})')
                    continue

                if matches:
                    if len(matches) == 0:
                        print('db_get_all_clan_stats(): No crucible matches played recently')
                        continue

                    if not _character.last_pvp_match:
                        #print('db_get_all_clan_stats(): no crucible match ever played. setting last_pvp_match to 0.')
                        _character.last_pvp_match = 0
                        try:
                            self.db.session.commit()
                        except Exception as e:
                            self.db.session.rollback()

                    for match in matches:
                        if int(match) > int(_character.last_pvp_match):
                            matches_to_process.append(int(match))
                            #print(f'db_get_all_clan_stats(): Found new match to process: {match}')

                    print('New matches found. Processing.')
                    #print(f'\n-------------\ndb_get_all_clan_stats(): Processing matches for Player: {player.name} ({member}) - Character: {_character.char_id} - Last match: {_character.last_pvp_match}')
                    for match_ in matches_to_process:
                        #print(f'db_get_all_clan_stats(): Processing match {match_}')
                        self.db_update_match(char, match_) # API call count - 3 (depends on how many matches are processed)
                        api_calls = api_calls + 1

                        if not nosave:
                            self.download_pgcr(member.membership_id, char, match_)
                            api_calls = api_calls + 1

            self.db_update_player_last_played(member.membership_id, member.membership_type)
            api_calls = api_calls + 1
            print(f'Total API calls: {api_calls}')
            self.update_player_last_updated(member.membership_id)
        print('Done.')
        print(datetime.now() - start_time)

    def db_is_alive(self):
        try:
            self.query_destiny_db(f'SELECT json FROM DestinyInventoryItemDefinition WHERE id = -665975637')
            return True
        except:
            print('Destiny 2 DB not found! Skipping.')
            return False

    def db_update_stats(self, membership_id, membership_type, online_status):
        """Update triumph, power, etc for a player."""
        try:
            profile = self.get_profile_all(membership_id, membership_type)
        except Exception as e:
            print(f'Failed to retrieve profile for {membership_id} (type: {membership_type})')
            return

        try:
            player = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()
        except Exception as e:
            print(f'{membership_id} not found in database. Reason: {e}')
            return False

        # Update the player's triumph if the current value is higher than the value in the database
        # TODO: move to its own function
        current_triumph = profile['Response']['profileRecords']['data']['score']
        if player.triumph:
            if current_triumph > player.triumph:
                player.triumph = current_triumph
        else:
            player.triumph = current_triumph

        try:
            self.db.session.commit()
        except Exception as e:
            logging.error(f'db_update_stats(): {membership_id}: failed to commit new stats. {e}')
            self.db.session.rollback()

        # Update the player's owned exotic collectibles
        self.get_profile_weapons(membership_id, profile)

        # Update the player's seals
        self.get_seals(membership_id, profile)

        self.get_player_activity()

        # TODO: move to its own function
        # TODO: Some profiles report more than one active currentActivityHash. Compare dateActivityStarted between the two and use the most recent one
        if online_status:
            current_activity = self.get_current_activity(profile['Response']['characterActivities']['data'])
            if current_activity:
                now = datetime.utcnow()
                activity_start_time = current_activity['dateActivityStarted']
                activity_name = current_activity['currentActivityHash']
                player.last_activity = activity_name
                player.last_activity_time = activity_start_time
                player.online = True
                #print(f'Player {player.name} ({membership_id}) | Now: {now} | Activity: {activity_name} started {activity_start_time}')
        else:
            now = datetime.utcnow()
            date_last_played = profile['Response']['profile']['data']['dateLastPlayed']
            #print(f'Player {player.name} ({membership_id}) | Now: {now} | Last played {date_last_played}')
            player.last_activity_time = date_last_played
            player.online = False

        try:
            self.db.session.commit()
        except Exception as e:
            print(f'Failed to commit last activity information. Reason: {e}')
            self.db.session.rollback()

        # Update character power
        self.get_characters_power(membership_id, profile)

        self.db_update_player_last_played(membership_id, membership_type)
        self.update_player_last_updated(membership_id)

    # Section: DEFINITIONS - ACTIVITIES
    def get_definition_activity(self, activity_hash):
        """TODO: have to loop through all chars to get the current activity hash."""
        activity_hash = self.get_hash(activity_hash)
        if activity_hash == 82913930:
            return "Orbit"

        try:
            query = self.query_destiny_db(f'SELECT json FROM DestinyActivityDefinition WHERE id = {activity_hash}')
            return query['displayProperties']['name']
        except Exception as e:
            print(f'Failed to get activity information for {activity_hash}.')
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
                current_activity_date = character_data[k]['dateActivityStarted']
                current_activities.append({'currentActivityHash': current_activity, 'dateActivityStarted': current_activity_date})
        
        if len(current_activities) > 1:
            return sorted(current_activities, key=lambda k: k['dateActivityStarted'], reverse=True)[0]
        elif current_activities:
            return current_activities[0]
        else:
            return

    def get_player_activity(self, character_data, online):
        


    def db_update_match(self, char, match_id):
        if not self.db_is_alive():
            return

        print(f'db_update_match(): match_id passed in from db_get_all_clan_stats -> {match_id}')
        match = self.get_pgcr(match_id) # API call count - 1
        if 'Response' not in match:
            print('No response')
            return
        if 'entries' not in match['Response']:
            print('No entries in match, skipping.')
            return

        _entries = match['Response']['entries']
        matchtime = match['Response']['period']
        matchtime = matchtime.replace('T', ' ')[:-1]
        matchtime = datetime.strptime(matchtime, '%Y-%m-%d %H:%M:%S')
        #match_id = int(match['Response']['activityDetails']['instanceId'])
        #print(f'db_update_match(): Processing match {match_id}')
        char = str(char)
        _character = self.db.session.query(Characters).filter(Characters.char_id==char).first()
        player = self.db.session.query(Players).join(Characters).filter(Characters.char_id==char).first()

        for entry in _entries:
            # break this characterId if check so that it returns, remove it from the for loop
            if str(char) in entry['characterId']:
                if 'weapons' not in entry['extended']:
                    print('No weapons to process')
                    continue

                '''
                # This was for when I was grinding to 2100 Glory. Don't need it to run anymore, but commenting out in case I use it for future functions
                if 69 in match['Response']['activityDetails']['modes']:
                    if char == '2305843009354414197':
                        print('Found comp game. Updating KD & KDA stats')
                        kd_stat_value = round(entry['values']['killsDeathsRatio']['basic']['value'], 2)
                        kda_stat_value = round(entry['values']['killsDeathsAssists']['basic']['value'], 2)
                        new_row_kd = Stats(parent_player=3, stat='kd', value=kd_stat_value, timestamp=matchtime)
                        new_row_kda = Stats(parent_player=3, stat='kda', value=kda_stat_value, timestamp=matchtime)
                        previous_kd = self.db.session.query(func.avg(Stats.value).label('avg')).filter(Stats.stat=='kd').filter(Stats.timestamp<=matchtime).first()
                        previous_kda = self.db.session.query(func.avg(Stats.value).label('avg')).filter(Stats.stat=='kda').filter(Stats.timestamp<=matchtime).first()
                        if previous_kd.avg:
                            new_kd_avg = round(float(str(previous_kd.avg)), 2)
                        else:
                            new_kd_avg = kd_stat_value

                        if previous_kda.avg:
                            new_kda_avg = round(float(str(previous_kda.avg)), 2)
                        else:
                            new_kda_avg = kda_stat_value
                        
                        new_row_kd_avg = Stats(parent_player=3, stat='kd_avg', value=new_kd_avg, timestamp=matchtime)
                        new_row_kda_avg = Stats(parent_player=3, stat='kda_avg', value=new_kda_avg, timestamp=matchtime)
                        try:
                            self.db.session.add_all([new_row_kd, new_row_kda, new_row_kd_avg, new_row_kda_avg])
                            self.db.session.commit()
                        except Exception as e:
                            print(e)
                            self.db.session.rollback
                '''

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
                        _item = self.query_destiny_db(f'SELECT json FROM DestinyInventoryItemDefinition WHERE id = {weapon_id}')
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

                    all_weapons = [weap.name for weap in self.db.session.query(Weapons).all()]
                    if name not in all_weapons:
                        # Add the weapon to our database if it does not exist
                        new = Weapons(name=name, damage_type=weapon_type, weapon_id=weapon_id, gun_type=subtype)
                        self.db.session.add(new)
                        self.db.session.commit()

                    _weap = self.db.session.query(Weapons).filter(Weapons.name==name).first()
                    new_weapon_entry = WeaponsData(kills=kills, match_time=matchtime, parent_id=_character.id, parent_weapon=_weap.id)
                    self.db.session.add(new_weapon_entry)

                    # TODO: maybe helper functions?
                    #   * add_weapon(<add a new weapons stats>)
                    #   * update_weapon(insert new weapond data)

        print(f'{match_id}: match successfully processed')
        _character.last_pvp_match = str(match_id)

        # TODO: only update if there is new data - What was this referring to?
        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()

    # Section: CLASSIFIED WEAPON HANDLING
    def classified_weapon_check(self):
        classified_weapons = self.db.session.query(Weapons).filter(Weapons.name=='Classified').all()
        for weapon in classified_weapons:
            query = self.query_destiny_db(f'SELECT json FROM DestinyInventoryItemDefinition WHERE id = {weapon.weapon_id}')
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
        collection = self._get(f'https://www.bungie.net/Platform/Destiny2/4/Profile/{membership_id}/Character/{character_id}/Collectibles/{presentation_node}/?components=800')
        return collection

    def get_collection_char_weapons(self, membership_id, character_id):
        """
        Retrieve weapon collectibles from a character.
        """
        collection = self._get(f'https://www.bungie.net/Platform/Destiny2/4/Profile/{membership_id}/Character/{character_id}/Collectibles/2214408526/?components=800')
        return collection

    def get_collection_profile(self, membership_id, membership_type):
        """
        Retrieve a profile's collection.
        """
        collection = self._get(f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=800')

        if collection['ErrorCode'] != 1:
            print(f'Error retrieving collection for {membership_id}')
            return

        return collection

    def get_collection_profile_exotic_weapons(self, membership_id):
        PRESENTATION_NODE_WEAPON_HASHES = [3919988882, 2969886327, 1139971093]
        collection = self.get_collection_profile(membership_id)
        player = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()

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

        exotic_weapon_collectibles = self.query_destiny_db_many('SELECT json FROM DestinyCollectibleDefinition')
        for collectible in exotic_weapon_collectibles:
            data = json.loads(collectible[0])
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
                db_collectible = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.collectible_hash==collectible_hash).first()
                db_collectible.expansion_id = expansion
                self.db.session.commit()
                '''

                db_collectibles = self.db.session.query(CollectiblesGame).all()
                db_collectibles_list = [exotic.collectible_hash for exotic in db_collectibles]
                if collectible_hash not in db_collectibles_list:
                    print(f'New collectible: {collectible_name} ({collectible_hash})')
                    new_collectible = CollectiblesGame(collectible_hash=collectible_hash, name=collectible_name, item_hash=collectible_item_hash, presentation_node_type=str(PRESENTATION_NODE_TYPE_WEAPONS), parent_presentation_node_hash=str(node_hash), icon_url=collectible_icon_url, expansion_id=expansion)
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

        player = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()

        # Profile-level collectibles
        for k,v in data['Response']['profileCollectibles']['data']['collectibles'].items():

            # Skip the collectible if we do not own it. If this result is odd, we do not own the collectible
            if v['state'] % 2 != 0:
                continue
            
            collectible_definition = self.db_get_collectible_definition(k)

            if collectible_definition['redacted']:
                print(f'Redacted collectible definition: {k}')
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

                player_collectibles = self.db.session.query(CollectiblesGame).join(CollectiblesPlayer).join(Players).filter(Players.membership_id==membership_id).all()
                player_collectibles_list = [_collectible.collectible_hash for _collectible in player_collectibles]
                if collectible_hash not in player_collectibles_list:
                    parent = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.collectible_hash==collectible_hash).first()
                    if not parent:
                        print(f'Collectible {collectible_hash}: No parent to attach to. Skipping. P.S. update the DB!')
                        continue

                    print(f'New collectible for {player.name}: {collectible_name}')
                    now = datetime.now()
                    new_collectible = CollectiblesPlayer(parent_player=player.id, date_collected=now)
                    parent.child_collectible.append(new_collectible)
                    try:
                        self.db.session.commit()
                    except Exception as e:
                        self.db.session.rollback()
                        print(f'Error adding new collectible {collectible_name} for {player.name}')

        # Character-level collectibles
        characters = [character for character in data['Response']['characterCollectibles']['data']]

        for character in characters:
            #print(f'Checking {character}')

            # By checking for the collectible on every character, we can skips the remaining unprocessed characters if its found on the 1st character
            player_collectibles = self.db.session.query(CollectiblesGame).join(CollectiblesPlayer).join(Players).filter(Players.membership_id==membership_id).all()
            player_collectibles_list = [_collectible.collectible_hash for _collectible in player_collectibles]
            if POLARIS_LANCE in player_collectibles_list:
                continue

            for k,v in data['Response']['characterCollectibles']['data'][str(character)]['collectibles'].items():
                if k == POLARIS_LANCE:
                    if v['state'] % 2 != 0:
                        print(f'New collectible for {player.name}: Polaris Lance')
                        now = datetime.now()
                        new_collectible = CollectiblesPlayer(parent_player=player.id, date_collected=now)
                        parent = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.collectible_hash==POLARIS_LANCE).first()
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
        player = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()

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

                player_collectibles = self.db.session.query(CollectiblesGame).join(CollectiblesPlayer).join(Players).filter(Players.membership_id==membership_id).all()
                player_collectibles_list = [_collectible.collectible_hash for _collectible in player_collectibles]
                if collectible_hash not in player_collectibles_list:
                    parent = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.collectible_hash==collectible_hash).first()
                    if not parent:
                        print(f'Collectible {collectible_hash}: No parent to attach to. Skipping.')
                        continue

                    print(f'New collectible for {player.name}: {collectible_name}')
                    now = datetime.now()
                    new_collectible = CollectiblesPlayer(parent_player=player.id, date_collected=now)
                    parent.child_collectible.append(new_collectible)
                    self.db.session.commit()

        # Character-level collectibles
        characters = [character for character in collection['Response']['characterCollectibles']['data']]

        for character in characters:
            #print(f'Checking {character}')

            # By checking for the collectible on every character, we can skips the remaining unprocessed characters if its found on the 1st character
            player_collectibles = self.db.session.query(CollectiblesGame).join(CollectiblesPlayer).join(Players).filter(Players.membership_id==membership_id).all()
            player_collectibles_list = [_collectible.collectible_hash for _collectible in player_collectibles]
            if POLARIS_LANCE in player_collectibles_list:
                continue

            for k,v in collection['Response']['characterCollectibles']['data'][str(character)]['collectibles'].items():
                if k == POLARIS_LANCE:
                    if v['state'] % 2 != 0:
                        print(f'New collectible for {player.name}: Polaris Lance')
                        now = datetime.now()
                        new_collectible = CollectiblesPlayer(parent_player=player.id, date_collected=now)
                        parent = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.collectible_hash==POLARIS_LANCE).first()
                        parent.child_collectible.append(new_collectible)
                        self.db.session.commit()

    def db_update_player_collectible_weapons(self):
        """
        Updates all owned Exotic Weapons for each Player in the clan.
        """
        self.get_collectible_exotic_weapons()
        clan_members = self.db_get_clan_member_ids()
        for clan_member in clan_members:
            print(clan_member)
            self.get_collection_profile_weapons(clan_member)

    def db_get_collection_exotic_weapons_unowned(self):
        players = [player.id for player in self.db.session.query(Players).all()]
        unowned_exotics = self.db.session.query(CollectiblesGame).filter(~CollectiblesGame.child_collectible.any(CollectiblesPlayer.parent_player.in_(players))).all()
        return unowned_exotics

    def api_get_collectible_exotics_unowned(self):
        players = [player.id for player in self.db.session.query(Players).all()]
        unowned_exotics = self.db.session.query(CollectiblesGame).filter(~CollectiblesGame.child_collectible.any(CollectiblesPlayer.parent_player.in_(players))).order_by(CollectiblesGame.expansion_id.desc()).all()
        results = self.collectibles_schema.dump(unowned_exotics)
        return jsonify(results.data)

    def db_get_collection_exotic_weapons_owned(self):
        players = [player.id for player in self.db.session.query(Players).all()]
        owned_exotics = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.child_collectible.any(CollectiblesPlayer.parent_player.in_(players))).all()
        all_data = []        
        for exotic in owned_exotics:
            owners = self.db_get_collectible_exotic_weapon_owners(exotic.collectible_hash)
            owners_list = [owner.name for owner in owners]
            all_data.append(DestinyWeaponOwners(weapon=exotic, owners=owners_list))

        return all_data

    def api_get_collectible_exotics_owned(self):
        players = [player.id for player in self.db.session.query(Players).all()]
        owned_exotics = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.child_collectible.any(CollectiblesPlayer.parent_player.in_(players))).order_by(CollectiblesGame.expansion_id.desc()).all()
        all_data = []        
        for exotic in owned_exotics:
            owners = self.db_get_collectible_exotic_weapon_owners(exotic.collectible_hash)
            owners_list = [owner.name for owner in owners]
            dwo = DestinyWeaponOwners(weapon=exotic, owners=owners_list).serialize()
            all_data.append(dwo)

        return all_data

    def db_get_collectible(self, collectible_hash):
        collectible = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.collectible_hash==collectible_hash).first()
        owners = self.db_get_collectible_exotic_weapon_owners(collectible_hash)
        owners_list = [owner.name for owner in owners]
        obj = DestinyWeaponOwners(weapon=collectible, owners=owners_list)
        return obj.serialize()

    def db_exotic_owners(self):
        players = [player.id for player in self.db.session.query(Players).all()]
        exotics = self.db.session.query(CollectiblesGame, Players).join(CollectiblesPlayer).join(Players).group_by(CollectiblesGame.id, Players.id).filter(CollectiblesGame.child_collectible.any(CollectiblesPlayer.parent_player != None)).all()
        return exotics

    def db_reset_collectibles(self):
        """
        Deletes all Collectible information from the database.
        """
        self.db.session.query(CollectiblesPlayer).delete()
        self.db.session.commit()
        self.db.session.query(CollectiblesGame).delete()
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
        owners = self.db.session.query(Players).join(CollectiblesPlayer).join(CollectiblesGame).filter(CollectiblesGame.collectible_hash==collectible_hash).all()
        return owners

    def db_get_collectible_exotic_weapons_for_player(self, membership_id):
        """
        Retrieves all exotic weapon collectibles owned by a player.
        """
        owned_exotics = self.db.session.query(CollectiblesGame).join(CollectiblesPlayer).join(Players).filter(Players.membership_id==membership_id).all()
        return owned_exotics

    def db_get_collectible_exotic_weapons_for_player_unowned(self, membership_id):
        player_id = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()
        unowned_exotics = self.db.session.query(CollectiblesGame).filter(~CollectiblesGame.child_collectible.any(CollectiblesPlayer.parent_player==player_id.id)).all()
        return unowned_exotics

    def db_get_collectible_exotic_weapons_for_player_owned(self, membership_id):
        player_id = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()
        owned_exotics = self.db.session.query(CollectiblesGame).filter(CollectiblesGame.child_collectible.any(CollectiblesPlayer.parent_player==player_id.id)).all()
        return owned_exotics

    def db_get_collectible_exotic_weapons_per_player(self):
        """
        Returns the number of exotics owned per player.
        """
        exotics_owned_count = self.db.session.query(Players.name, func.count(CollectiblesPlayer.id)).group_by(Players.name).filter(CollectiblesPlayer.parent_player==Players.id).order_by(func.count(CollectiblesPlayer.id).desc()).all()
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
        weapon_type = self.get_bucket(_hash)
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
        return self.db.session.query(Players).filter(Players.membership_id==membership_id).first()

    def api_get_player(self, membership_id):
        player = self.db.session.query(Players.name, Players.membership_id, Players.last_activity, Players.triumph, func.max(Characters.power).label("highest_power")) \
            .join(Characters) \
            .group_by(Players.name, Players.membership_id, Players.last_activity, Players.triumph) \
            .filter(Players.membership_id==membership_id) \
            .order_by(func.max(Characters.power).label("highest_power").desc()) \
            .first()
        player = self.player_schema.dump(player)
        return jsonify(player.data)

    def get_player_characters_power(self, player_name):
        return self.db.session.query(Characters).join(Players).filter(Players.name==player_name).order_by(Characters.power.desc()).all()

    def api_get_char_kills(self, membership_id, days):
        if days == 0:
            query = self.db.session.query(Characters.class_name, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .join(Players) \
                .group_by(Characters.class_name) \
                .filter(Players.membership_id==membership_id) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            results = self.character_schema.dump(query)
            return jsonify(results.data)
        elif days > 0:
            time_range = datetime.now() - timedelta(days=days)
            query = self.db.session.query(Characters.class_name, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .join(Players) \
                .group_by(Characters.class_name) \
                .filter(Players.membership_id==membership_id) \
                .filter(WeaponsData.match_time >= time_range) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            results = self.character_schema.dump(query)
            return jsonify(results.data)

    def get_player_characters_kills(self, player_name, days):
        if days == 0:
            return self.db.session.query(Characters.class_name, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .join(Players) \
                .group_by(Characters.class_name) \
                .filter(Players.name==player_name) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
        elif days > 0:
            time_range = datetime.now() - timedelta(days=days)
            return self.db.session.query(Characters.class_name, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .join(Players) \
                .group_by(Characters.class_name) \
                .filter(Players.name==player_name) \
                .filter(WeaponsData.match_time >= time_range) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()

    def get_player_character_id(self, player_id):
        character_id = self.db.session.query(Characters).join(Players).filter(Players.membership_id==str(player_id)).first()
        if character_id:
            return character_id.char_id
        else:
            return

    def get_player_weapons(self, membership_id):
        weapons = self.db.session.query(Weapons.name, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
            .join(WeaponsData) \
            .join(Characters) \
            .join(Players) \
            .group_by(Weapons.name, Weapons.weapon_id) \
            .filter(Players.membership_id==membership_id) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        return weapons

    def api_get_player_weapons(self, membership_id, days):
        if days == 0:
            weapons = self.db.session.query(Weapons.name, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .join(Characters) \
                .join(Players) \
                .group_by(Weapons.name, Weapons.weapon_id) \
                .filter(Players.membership_id==membership_id) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            results = self.player_weapon_schema.dump(weapons)
            return jsonify(results.data)
        elif days > 0:
            time_range = datetime.now() - timedelta(days=days)
            weapons = self.db.session.query(Weapons.name, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .join(Characters) \
                .join(Players) \
                .group_by(Weapons.name, Weapons.weapon_id) \
                .filter(Players.membership_id==membership_id) \
                .filter(WeaponsData.match_time >= time_range) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            results = self.player_weapon_schema.dump(weapons)
            return jsonify(results.data)

    def get_player_weapons_days(self, membership_id, days):
        if days == 0:
            weapons = self.db.session.query(Weapons.name, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(WeaponsData) \
                .join(Characters) \
                .join(Players) \
                .group_by(Weapons.name, Weapons.weapon_id) \
                .filter(Players.membership_id==membership_id) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            return weapons

        month = datetime.now() - timedelta(days=days)
        weapons = self.db.session.query(Weapons.name, Weapons.weapon_id, func.sum(WeaponsData.kills).label('total_kills')) \
            .join(WeaponsData) \
            .join(Characters) \
            .join(Players) \
            .group_by(Weapons.name, Weapons.weapon_id) \
            .filter(Players.membership_id==membership_id) \
            .filter(WeaponsData.match_time >= month) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        return weapons

    def get_top_weapon_by_type(self, weapon_type):
        if weapon_type not in self.WEAPON_TYPES:
            print('Invalid weapon type. Valid weapon types: kinetic, energy, power')
            return

        results = self.db.session.query(Weapons.name, func.sum(WeaponsData.kills).label("total_kills"), Weapons.weapon_id) \
            .join(WeaponsData) \
            .group_by(Weapons.name, Weapons.weapon_id) \
            .filter(Weapons.damage_type==weapon_type) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        return results

    def get_top_weapon_by_type_days(self, weapon_type, days):
        if weapon_type not in self.WEAPON_TYPES:
            print('Invalid weapon type. Valid weapon types: kinetic, energy, power')
            return

        if days == 0:
            results = self.db.session.query(Weapons.name, func.sum(WeaponsData.kills).label("total_kills"), Weapons.weapon_id) \
                .join(WeaponsData) \
                .group_by(Weapons.name, Weapons.weapon_id) \
                .filter(Weapons.damage_type==weapon_type) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            return results

        timerange = datetime.now() - timedelta(days=days)
        results = self.db.session.query(Weapons.name, func.sum(WeaponsData.kills).label("total_kills"), Weapons.weapon_id) \
            .join(WeaponsData) \
            .group_by(Weapons.name, Weapons.weapon_id) \
            .filter(Weapons.damage_type==weapon_type) \
            .filter(WeaponsData.match_time >= timerange) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        return results

    def api_get_all_weapons(self, days):
        if days == 0:
            results = self.db.session.query(Weapons.name, func.sum(WeaponsData.kills).label("total_kills"), Weapons.weapon_id) \
                .join(WeaponsData) \
                .group_by(Weapons.name, Weapons.weapon_id) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            results = self.weapon_type_kills_schema.dump(results)
            return jsonify(results.data)

        timerange = datetime.now() - timedelta(days=days)
        results = self.db.session.query(Weapons.name, func.sum(WeaponsData.kills).label("total_kills"), Weapons.weapon_id) \
            .join(WeaponsData) \
            .group_by(Weapons.name, Weapons.weapon_id) \
            .filter(WeaponsData.match_time >= timerange) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        results = self.weapon_type_kills_schema.dump(results)
        return jsonify(results.data)

    def api_get_top_weapon_by_type(self, weapon_type, days):
        if weapon_type not in self.WEAPON_TYPES:
            print('Invalid weapon type. Valid weapon types: kinetic, energy, power')
            return

        if days == 0:
            results = self.db.session.query(Weapons.name, func.sum(WeaponsData.kills).label("total_kills"), Weapons.weapon_id) \
                .join(WeaponsData) \
                .group_by(Weapons.name, Weapons.weapon_id) \
                .filter(Weapons.damage_type==weapon_type) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            results = self.weapon_type_kills_schema.dump(results)
            return jsonify(results.data)

        timerange = datetime.now() - timedelta(days=days)
        results = self.db.session.query(Weapons.name, func.sum(WeaponsData.kills).label("total_kills"), Weapons.weapon_id) \
            .join(WeaponsData) \
            .group_by(Weapons.name, Weapons.weapon_id) \
            .filter(Weapons.damage_type==weapon_type) \
            .filter(WeaponsData.match_time >= timerange) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        results = self.weapon_type_kills_schema.dump(results)
        return jsonify(results.data)

    def get_weapon_name(self, weapon_id):
        name = self.db.session.query(Weapons.name).filter(Weapons.weapon_id==weapon_id).first()
        if name:
            return name.name
        else:
            return

    def api_get_weapon(self, weapon_id):
        query = self.db.session.query(Weapons).filter(Weapons.weapon_id==weapon_id).first()
        results = self.weapon_schema.dump(query)
        return jsonify(results.data)

    def api_get_weapon_kills(self, weapon_id, days):
        """
        Returns all kills (in the provided date range) by every Player for a specific Weapon.
        0 days = lifetime kills
        """
        if days == 0:
            weapon_stats = self.db.session.query(Players.name, Players.membership_id, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(Characters) \
                .join(WeaponsData) \
                .join(Weapons) \
                .group_by(Players.name, Players.membership_id) \
                .filter(Weapons.weapon_id==weapon_id) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            results = self.weapon_kills_schema.dump(weapon_stats)
            return jsonify(results.data)

        time_range = datetime.now() - timedelta(days=days)
        weapon_stats = self.db.session.query(Players.name, Players.membership_id, func.sum(WeaponsData.kills).label('total_kills')) \
            .join(Characters) \
            .join(WeaponsData) \
            .join(Weapons) \
            .group_by(Players.name, Players.membership_id) \
            .filter(Weapons.weapon_id==weapon_id) \
            .filter(WeaponsData.match_time >= time_range) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()

        results = self.weapon_kills_schema.dump(weapon_stats)
        return jsonify(results.data)

    def get_weapon_kills_days(self, weapon_id, days):
        """
        Returns all kills (in the provided date range) by every Player for a specific Weapon.
        0 days = lifetime kills
        """
        if days == 0:
            weapon_stats = self.db.session.query(Players.name, Players.membership_id, func.sum(WeaponsData.kills).label('total_kills')) \
                .join(Characters) \
                .join(WeaponsData) \
                .join(Weapons) \
                .group_by(Players.name, Players.membership_id) \
                .filter(Weapons.weapon_id==weapon_id) \
                .order_by(func.sum(WeaponsData.kills).desc()) \
                .all()
            return weapon_stats

        time_range = datetime.now() - timedelta(days=days)
        weapon_stats = self.db.session.query(Players.name, Players.membership_id, func.sum(WeaponsData.kills).label('total_kills')) \
            .join(Characters) \
            .join(WeaponsData) \
            .join(Weapons) \
            .group_by(Players.name, Players.membership_id) \
            .filter(Weapons.weapon_id==weapon_id) \
            .filter(WeaponsData.match_time >= time_range) \
            .order_by(func.sum(WeaponsData.kills).desc()) \
            .all()
        return weapon_stats

    def download_pgcr(self, player, character, match_id):
        """
        Download a PGCR to a .json file. Stored in <project root>/data/pgcr/<player>/<character>
        """
        directory = Path(f'./data/pgcr/{player}/{character}')
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

        pgcr = self.get_pgcr(match_id)
        self.save_file(pgcr, match_id, directory)

    def download_pgcr_clan_history(self):
        members = self.db_get_clan_members()
        for member in members:
            characters = self.db_get_character_ids(member.membership_id)
            for character in characters:
                matches = self.get_crucible_history(member.membership_id, character)
                if matches:
                    for match in matches:
                        self.download_pgcr(member.membership_id, character, match)
                else:
                    print('No matches. Skipping.')

    def download_pgcr_history_crucible(self, membership_id, character_id):
        matches = self.get_crucible_history(membership_id, character_id)
        pgcr_dir = Path('./data/pgcr')
        if not pgcr_dir:
            print('PGCR data directory does not exist. Creating')
            pgcr_dir.mkdir()

        # Create a new directory for the player
        player_dir = pgcr_dir / f'{membership_id}'
        if not player_dir.exists():
            print('Player directory does not exist. Creating.')
            player_dir.mkdir()

        # Create a new directory for the player's character
        character_dir = pgcr_dir / f'{membership_id}' / f'{character_id}'
        if not character_dir.exists():
            print('Character directory does not exist. Creating.')
            character_dir.mkdir()

        saved_matches = [match.name.split('.')[0] for match in list(character_dir.glob('*.json'))]

        # Get each match and save to json file
        for match in matches:
            if match not in saved_matches:
                print('Match not saved. Saving')
                pgcr = self.get_pgcr(match)
                self.save_file(pgcr, match, character_dir)
            else:
                print('Match already saved. Skipping.')

    def get_activities(self, membership_id, character_id):
        page = 0
        max_pages = 100
        count = 250
        all_activities = []

        for p in range(max_pages):
            activities = self._get(f'https://www.bungie.net/Platform/Destiny2/4/Account/{membership_id}/Character/{character_id}/Stats/Activities/?mode=5&page={p}&count={count}')
            if 'activities' in activities['Response']:
                print(f'Page: {p}')
                for activity in activities['Response']['activities']:
                    #date = activity['period']
                    instance_id = activity['activityDetails']['instanceId']
                    all_activities.append(instance_id)
                    #print(f'{date}: {instance_id}')
            else:
                print('No results. Stopping.')
                break
            print(len(activities['Response']['activities']))
            sleep(1)
        print('Break happened, this ran.')
        all_activities = list(reversed(all_activities))
        for act in all_activities:
            print(act)
        #return activities

    def db_reset_all(self):
        """
        Effectively wipes out all match related data for all characters. Resets each characters' last match played value, and wipes out all entries in WeaponsData.
        """
        if not self.db_is_alive():
            return

        self.db.session.query(WeaponsData).delete()
        all_chars = self.db.session.query(Characters).all()
        for char in all_chars:
            char.last_pvp_match = 0

        try:
            self.db.session.commit()
            print('Set all characters last_pvp_match to 0')
            print('Deleted all entires in WeaponsData')
        except Exception as e:
            self.db.session.rollback()

    def parse_local_json(self, player, char):
        """
        Example on how to parse local JSON files.
        """
        # Check if player/char exists first
        player_db = self.db.session.query(Players).filter(Players.membership_id==player).first()
        if not player:
            return 'Player does not exist.'

        character = self.db.session.query(Characters).filter(Characters.char_id==char).first()
        if not character:
            return 'Character does not exist.'

        pgcr_dir = Path(f'./data/pgcr/{player}/{char}')
        if not pgcr_dir.exists():
            return 'Directory does not exist.'

        for pgcr in pgcr_dir.iterdir():
            with pgcr.open('r', encoding='utf-8') as datafile:
                data = json.load(datafile)
                if 69 in data['Response']['activityDetails']['modes']:
                    for entry in data['Response']['entries']:
                        if char in entry['characterId']:
                            match_time = data['Response']['period']
                            match_time = match_time.replace('T', ' ')[:-1]
                            match_time_obj = datetime.strptime(match_time, '%Y-%m-%d %H:%M:%S')
                            match_time = datetime.strftime(match_time_obj, '%Y-%m-%d %H:%M:%S')
                            kd_stat_value = round(entry['values']['killsDeathsRatio']['basic']['value'], 2)
                            kda_stat_value = round(entry['values']['killsDeathsAssists']['basic']['value'], 2)

                            new_row_kd = Stats(parent_player=player_db.id, stat='kd', value=kd_stat_value, timestamp=match_time_obj)
                            new_row_kda = Stats(parent_player=player_db.id, stat='kda', value=kda_stat_value, timestamp=match_time_obj)

                            try:
                                self.db.session.add_all([new_row_kd, new_row_kda])
                                print(f'New entry | {match_time}: KD {kd_stat_value} - KDA {kda_stat_value}')
                                self.db.session.commit()
                            except Exception as e:
                                print(e)
                                self.db.session.rollback
    
    # SECTION: Stats - calculating
    def calculate_kd_history(self):
        """
        Add the new AVG K/D to the database by taking the average of all previous values.
        """
        stats_all = self.db.session.query(Stats).filter(Stats.stat=='kda').order_by(Stats.timestamp.asc()).all()
        for stat in stats_all:
            if stat == stats_all[0]:
                # This is the first entry, so no need to calcuate the average here
                continue
            
            previous_stats = self.db.session.query(func.avg(Stats.value).label('avg')).filter(Stats.stat=='kda').filter(Stats.timestamp<=stat.timestamp).first()
            new_value = round(float(str(previous_stats.avg)), 2)
            new_row = Stats(parent_player=stat.parent_player, stat='kda_avg', value=new_value, timestamp=stat.timestamp)
            self.db.session.add(new_row)
            self.db.session.commit()
            print(f'{stat.timestamp}: Average K/DA - {new_value} ')

    def get_new_matches(self, membership_id):
        """
        Retrieves new PGCR IDs for new Crucible matches played by clan members and sends them to Redis for processing by a worker.
        Returns a list of new matches played. Returns nothing if there are no matches played.
        """
        clan_member = self.db.session.query(Players).filter(Players.membership_id==membership_id).first()

        # TODO: Change this check to check last_activity_time
        if clan_member.last_played:
            last_played_api = self.get_player_last_played(clan_member.membership_id, clan_member.membership_type)
            if not last_played_api:
                print(f'{clan_member.name} ({clan_member.membership_id}): error retrieving profile information. Skipping')
                return

            last_played_api = datetime.strptime(last_played_api, '%Y-%m-%dT%H:%M:%SZ')

            if last_played_api == clan_member.last_played:
                print(f'{clan_member.name} ({clan_member.membership_id}): has not played since their last session. Skipping.')
                return

            redis_data = {}
            redis_data['membershipId'] = clan_member.membership_id
            redis_data['membershipType'] = clan_member.membership_type
            redis_data.setdefault('characters', [])

            characters = self.db_get_characters(clan_member.membership_id)
            if not characters:
                print(f'{clan_member.name} ({clan_member.membership_id}): no characters found. Skipping.')

            for character in characters:
                print(f'{character.class_name} ({character.char_id}): checking for new matches played.')
                latest_match = self.get_latest_pvp_activity_id(clan_member.membership_id, clan_member.membership_type, character.char_id)
                if latest_match:
                    if character.last_pvp_match == latest_match:
                        print('No new crucible matches played.')
                        return redis_data

                # TODO: https://jira.bonar.lab/browse/CLAN-125 - Add logic so we can check less pages
                matches = self.get_crucible_history(clan_member.membership_id, clan_member.membership_type, character.char_id)
                if not matches:
                    print('No crucible matches played.')
                    return redis_data

                matches_to_process = []
                for match in matches:
                    if int(match) > int(character.last_pvp_match):
                        matches_to_process.append(int(match))

                matches_to_process.sort()

                redis_data['characters'].append({'characterId': character.char_id, 'matches': matches_to_process})
                print(redis_data)
                return redis_data

class DestinyWeaponOwners(object):
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
    """Serialize a player object."""
    def __init__(self, player):
        self.player = player

    def serialize(self):
        last_activity_time = datetime.strftime(self.player.last_activity_time, '%Y-%m-%dT%H:%M:%SZ')
        if self.player.seals:
            return {
                'name': self.player.name,
                'membership_id': self.player.membership_id,
                'triumph': self.player.triumph,
                'last_activity': self.player.last_activity,
                'last_activity_time': last_activity_time,
                'highest_power': self.player.highest_power,
                'seals': [seal for seal in self.player.seals.split(',')],
                'online': self.player.online
            }
        else:
            return {
                'name': self.player.name,
                'membership_id': self.player.membership_id,
                'triumph': self.player.triumph,
                'last_activity': self.player.last_activity,
                'last_activity_time': last_activity_time,
                'highest_power': self.player.highest_power,
                'seals': [],
                'online': self.player.online
            }
