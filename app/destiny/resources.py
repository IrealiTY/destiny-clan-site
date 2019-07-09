from flask import request
from flask_restplus import Namespace, Resource, fields, marshal_with
from .client import DestinyAPI
from . import api_rest

d2 = DestinyAPI()

@api_rest.route('/resources/roster')
class ResourceRoster(Resource):
    def get(self):
        data = d2.api_get_roster()
        return data

@api_rest.route('/resources/player/<string:membership_id>')
class ResourcePlayer(Resource):
    def get(self, membership_id):
        data = d2.api_get_player(membership_id)
        return data

@api_rest.route('/resources/player/<string:membership_id>/weapons/<int:days>')
class ResourcePlayerWeapons(Resource):
    def get(self, membership_id, days):
        data = d2.api_get_player_weapons(membership_id, days)
        return data

@api_rest.route('/resources/player/<string:membership_id>/characters/<int:days>')
class ResourcePlayerCharacters(Resource):
    def get(self, membership_id, days):
        data = d2.api_get_char_kills(membership_id, days)
        return data

@api_rest.route('/resources/weapon/<string:weapon_id>')
class ResourceWeapon(Resource):
    def get(self, weapon_id):
        data = d2.api_get_weapon(weapon_id)
        return data

@api_rest.route('/resources/weapon/<string:weapon_id>/kills/<int:days>')
class ResourceWeaponKills(Resource):
    def get(self, weapon_id, days):
        data = d2.api_get_weapon_kills(weapon_id, days)
        return data

@api_rest.route('/resources/collectible/<string:collectible_hash>')
class ResourceColletible(Resource):
    def get(self, collectible_hash):
        data = d2.db_get_collectible(collectible_hash)
        return data

@api_rest.route('/resources/collectibles')
class ResourceCollectibles(Resource):
    def get(self):
        data = d2.api_get_collectible_exotics_owned()
        return data

@api_rest.route('/resources/collectibles/unowned')
class ResourceCollectiblesUnowned(Resource):
    def get(self):
        data = d2.api_get_collectible_exotics_unowned()
        return data

@api_rest.route('/resources/weapontypes/<string:weapontype>/<int:days>')
class ResourceWeaponTypes(Resource):
    def get(self, weapontype, days):
        if weapontype == 'all':
            data = d2.api_get_all_weapons(days)
        else:
            data = d2.api_get_top_weapon_by_type(weapontype, days)

        return data

@api_rest.route('/resources/weapons/<string:category>/<int:days>')
class ResourceWeaponCategoryKills(Resource):
    def get(self, category, days):
        category = ' '.join(category.split('_')).title()
        data = d2.api_get_weapon_category_kills(category, days)
        return data