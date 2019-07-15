import pytest
import sys

sys.path.append('c:\\work\\gitlab\\\destiny2api')

from app import create_app

@pytest.fixture(scope='module')
def client():
    app = create_app()
    app.config['Testing'] = True
    return app.test_client()

def test_api_roster(client):
    response = client.get('/api/resources/roster')
    assert response.status_code == 200

def test_api_player(client):
    response = client.get('/api/resources/player/4611686018470721488')
    assert response.status_code == 200

def test_api_player_weapons(client):
    response = client.get('/api/resources/player/4611686018470721488/weapons/1')
    assert response.status_code == 200

def test_api_player_character_kills(client):
    resposne = client.get('/api/resources/player/4611686018470721488/characters/1')

def test_api_weapon(client):
    response = client.get('/api/resources/weapon/347366834')
    assert response.status_code == 200

def test_api_weapon_kills(client):
    response = client.get('/api/resources/weapon/347366834/kills/1')
    assert response.status_code == 200

def test_api_weapon_kills_type(client):
    response = client.get('/api/resources/weapontypes/energy/1')
    assert response.status_code == 200

def test_api_weapon_kills_category(client):
    response = client.get('/api/resources/weapons/Hand%20Cannon/1')
    assert response.status_code == 200

def test_api_collectible(client):
    response = client.get('/api/resources/collectible/1660030047')
    assert response.status_code == 200

def test_api_collectibles_owned(client):
    response = client.get('/api/resources/collectibles')
    assert response.status_code == 200

def test_api_collectibles_unowned(client):
    response = client.get('/api/resources/collectibles/unowned')
    assert response.status_code == 200
