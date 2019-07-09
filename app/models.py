from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean
from flask_marshmallow import Marshmallow
import datetime
from config import Config

db = SQLAlchemy()
ma = Marshmallow()
print('db = SQLAlchemy()')

class Players(db.Model):
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    membership_id = Column(String)
    membership_type = Column(Integer)
    last_updated = Column(DateTime)
    last_played = Column(DateTime)
    triumph = Column(Integer)
    seals = Column(String)
    last_activity = Column(String)
    last_activity_time = Column(DateTime)
    join_date = Column(DateTime)
    online = Column(Boolean, default=False)
    children = relationship("Characters")
    children_stats = relationship("Stats")
    children_collectibles = relationship("CollectiblesPlayer")

class Stats(db.Model):
    __tablename__ = 'playerstats'
    id = Column(Integer, primary_key=True)
    parent_player = Column(Integer, ForeignKey('player.id'))
    glory = Column(Integer)
    stat = Column(String)
    value = Column(Numeric)
    timestamp = Column(DateTime)

class Characters(db.Model):
    __tablename__ = 'character'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('player.id'))
    char_id = Column(String)
    last_pvp_match = Column(String)
    class_name = Column(String)
    power = Column(Integer)
    children = relationship("WeaponsData")

class WeaponsData(db.Model):
    __tablename__ = 'weapondata'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('character.id'))
    parent_weapon = Column(Integer, ForeignKey('weapon.id'))
    kills = Column(Integer)
    match_time = Column(DateTime)

class Weapons(db.Model):
    __tablename__ = 'weapon'
    id = Column(Integer, primary_key=True)
    weapon_id = Column(String)
    name = Column(String)
    damage_type = Column(String)
    gun_type = Column(String)
    children = relationship("WeaponsData")

class Manifest(db.Model):
    __tablename__ = 'manifest'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    hash = Column(String)
    updated = Column(DateTime)

class CollectiblesPlayer(db.Model):
    __tablename__ = 'collectibles_player'
    id = Column(Integer, primary_key=True)
    parent_player = Column(Integer, ForeignKey('player.id'))
    parent_collectible = Column(Integer, ForeignKey('collectibles_game.id'))
    date_collected = Column(DateTime)

class CollectiblesGame(db.Model):
    __tablename__ = 'collectibles_game'
    id = Column(Integer, primary_key=True)
    collectible_hash = Column(String)
    item_hash = Column(String)
    icon_url = Column(String)
    name = Column(String)
    presentation_node_type = Column(String)
    parent_presentation_node_hash = Column(String)
    expansion_id = Column(Integer)
    child_collectible = relationship("CollectiblesPlayer")

class PlayerSchema(ma.Schema):
    class Meta:
        fields = ('name', 'membership_id', 'triumph', 'last_activity', 'highest_power', 'seals', 'online')

class PlayersSchema(ma.Schema):
    class Meta:
        ordered = True
        fields = ('name', 'membership_id', 'triumph', 'last_activity', 'last_activity_time', 'highest_power', 'seals', 'online')

class PlayerWeaponSchema(ma.Schema):
    class Meta:
        ordered = True
        fields = ('name', 'total_kills', 'weapon_id')

class CharacterSchema(ma.Schema):
    class Meta:
        ordered = True
        fields = ('class_name', 'total_kills')

class WeaponSchema(ma.Schema):
    class Meta:
        ordered = True
        fields = ('name', 'weapon_id', 'gun_type')

class WeaponKillsSchema(ma.Schema):
    class Meta:
        ordered = True
        fields = ('name', 'membership_id', 'total_kills')

class WeaponTypeKillsSchema(ma.Schema):
    class Meta:
        ordered = True
        fields = ('name', 'total_kills', 'weapon_id')

class CollectibleSchema(ma.Schema):
    class Meta:
        ordered = True
        fields = ('name', 'icon_url', 'item_hash', 'collectible_hash')

class WeaponCategoryKillsSchema(ma.Schema):
    class Meta:
        ordered = True
        fields = ('name', 'weapon_id', 'total_kills')