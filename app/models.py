from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean, JSON, PickleType
from flask_marshmallow import Marshmallow
from config import Config

db = SQLAlchemy()
ma = Marshmallow()

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
    title = Column(String)
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

class RaidStats(db.Model):
    __tablename__ = 'raidstats'
    id = Column(Integer, primary_key=True)
    parent_char = Column(Integer, ForeignKey('character.id'))
    pgcr_id = Column(String)
    activity = Column(String)
    activity_hash = Column(String)
    completed = Column(String)
    duration = Column(Integer)

class AggregateActivityStats(db.Model):
    __tablename__ = 'aggregateactivitystats'
    id = Column(Integer, primary_key=True)
    parent_char = Column(Integer, ForeignKey('character.id'))
    activity = Column(String)
    activity_hash = Column(String)
    completions = Column(Integer)
    seconds_played = Column(Integer)
    ms_fastest_run = Column(Integer)

class Characters(db.Model):
    __tablename__ = 'character'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('player.id'))
    char_id = Column(String)
    last_pvp_match = Column(String)
    class_name = Column(String)
    power = Column(Integer)
    children = relationship("WeaponsData")
    children_pgcr = relationship("PostGameCarnageReport")
    children_raidstats = relationship("RaidStats")

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

class PostGameCarnageReport(db.Model):
    __tablename__ = 'pgcr'
    id = Column(Integer, primary_key=True)
    pgcr_id = Column(String)
    data = Column(JSON)
    mode = Column(Integer)
    modes = Column(PickleType)
    date = Column(DateTime)
    parent_character = Column(Integer, ForeignKey('character.id'))

class DestinyEnemyRaceDefinition(db.Model):
    __tablename__ = 'DestinyEnemyRaceDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyPlaceDefinition(db.Model):
    __tablename__ = 'DestinyPlaceDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyActivityDefinition(db.Model):
    __tablename__ = 'DestinyActivityDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyActivityTypeDefinition(db.Model):
    __tablename__ = 'DestinyActivityTypeDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyClassDefinition(db.Model):
    __tablename__ = 'DestinyClassDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyGenderDefinition(db.Model):
    __tablename__ = 'DestinyGenderDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyInventoryBucketDefinition(db.Model):
    __tablename__ = 'DestinyInventoryBucketDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyRaceDefinition(db.Model):
    __tablename__ = 'DestinyRaceDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyTalentGridDefinition(db.Model):
    __tablename__ = 'DestinyTalentGridDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyUnlockDefinition(db.Model):
    __tablename__ = 'DestinyUnlockDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyMaterialRequirementSetDefinition(db.Model):
    __tablename__ = 'DestinyMaterialRequirementSetDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinySandboxPerkDefinition(db.Model):
    __tablename__ = 'DestinySandboxPerkDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyStatGroupDefinition(db.Model):
    __tablename__ = 'DestinyStatGroupDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyFactionDefinition(db.Model):
    __tablename__ = 'DestinyFactionDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyVendorGroupDefinition(db.Model):
    __tablename__ = 'DestinyVendorGroupDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyRewardSourceDefinition(db.Model):
    __tablename__ = 'DestinyRewardSourceDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyItemCategoryDefinition(db.Model):
    __tablename__ = 'DestinyItemCategoryDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyDamageTypeDefinition(db.Model):
    __tablename__ = 'DestinyDamageTypeDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyActivityModeDefinition(db.Model):
    __tablename__ = 'DestinyActivityModeDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyMedalTierDefinition(db.Model):
    __tablename__ = 'DestinyMedalTierDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyAchievementDefinition(db.Model):
    __tablename__ = 'DestinyAchievementDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyActivityGraphDefinition(db.Model):
    __tablename__ = 'DestinyActivityGraphDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyCollectibleDefinition(db.Model):
    __tablename__ = 'DestinyCollectibleDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyStatDefinition(db.Model):
    __tablename__ = 'DestinyStatDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyItemTierTypeDefinition(db.Model):
    __tablename__ = 'DestinyItemTierTypeDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyPresentationNodeDefinition(db.Model):
    __tablename__ = 'DestinyPresentationNodeDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyRecordDefinition(db.Model):
    __tablename__ = 'DestinyRecordDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyBondDefinition(db.Model):
    __tablename__ = 'DestinyBondDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyDestinationDefinition(db.Model):
    __tablename__ = 'DestinyDestinationDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyEquipmentSlotDefinition(db.Model):
    __tablename__ = 'DestinyEquipmentSlotDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyInventoryItemDefinition(db.Model):
    __tablename__ = 'DestinyInventoryItemDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyLocationDefinition(db.Model):
    __tablename__ = 'DestinyLocationDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyLoreDefinition(db.Model):
    __tablename__ = 'DestinyLoreDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyObjectiveDefinition(db.Model):
    __tablename__ = 'DestinyObjectiveDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyProgressionDefinition(db.Model):
    __tablename__ = 'DestinyProgressionDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyProgressionLevelRequirementDefinition(db.Model):
    __tablename__ = 'DestinyProgressionLevelRequirementDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinySackRewardItemListDefinition(db.Model):
    __tablename__ = 'DestinySackRewardItemListDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinySandboxPatternDefinition(db.Model):
    __tablename__ = 'DestinySandboxPatternDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinySeasonDefinition(db.Model):
    __tablename__ = 'DestinySeasonDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinySocketCategoryDefinition(db.Model):
    __tablename__ = 'DestinySocketCategoryDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinySocketTypeDefinition(db.Model):
    __tablename__ = 'DestinySocketTypeDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyVendorDefinition(db.Model):
    __tablename__ = 'DestinyVendorDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyMilestoneDefinition(db.Model):
    __tablename__ = 'DestinyMilestoneDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyActivityModifierDefinition(db.Model):
    __tablename__ = 'DestinyActivityModifierDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyReportReasonCategoryDefinition(db.Model):
    __tablename__ = 'DestinyReportReasonCategoryDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyPlugSetDefinition(db.Model):
    __tablename__ = 'DestinyPlugSetDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyChecklistDefinition(db.Model):
    __tablename__ = 'DestinyChecklistDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

class DestinyHistoricalStatsDefinition(db.Model):
    __tablename__ = 'DestinyHistoricalStatsDefinition'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    json = Column(JSON)

# API Schema
class PlayerSchema(ma.Schema):
    class Meta:
        fields = ('name', 'membership_id', 'triumph', 'last_activity', 'highest_power', 'seals', 'online', 'join_date')

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