from datetime import datetime
from app import models
from app import utilities
from app.utils import log

logger = log.get_logger(__name__)

def get_rumble_wins():
    start_time = datetime.now()
    """
    #All pvp matches for one character
    pvp_matches = models.db.session.query(models.PostGameCarnageReport) \
        .filter(models.PostGameCarnageReport.parent_character==41) \
        .filter(models.PostGameCarnageReport.mode==5) \
        .order_by(models.PostGameCarnageReport.date.desc()) \
        .all()
    """

    wins = 0
    winning_pgcrs = []

    pvp_matches = models.db.session.query(models.PostGameCarnageReport) \
        .join(models.Characters) \
        .filter(models.Characters.parent_id==17) \
        .filter(models.PostGameCarnageReport.mode==5) \
        .order_by(models.PostGameCarnageReport.date.desc()) \
        .all()
    
    print(f'Matches to process: {len(pvp_matches)}')

    characters = [char.char_id for char in models.db.session.query(models.Characters).filter(models.Characters.parent_id==17).all()]

    for match in pvp_matches:
        if 48 in match.data['Response']['activityDetails']['modes']:
            for e in match.data['Response']['entries']:
                if e['characterId'] in characters:
                    if e['score']['basic']['displayValue'] == '20':
                        wins = wins + 1
                        winning_pgcrs.append(match.pgcr_id)

    print(winning_pgcrs)
    print(len(winning_pgcrs))
    print(datetime.now() - start_time)
    return wins
