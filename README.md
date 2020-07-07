# Overview

**Update 6/26/2020: Unfortunately, the clan I made this for has disbanded so I have stopped work on the project. Leaving this here to showcase the work I have done.**

A Destiny 2 stat site made for my clan, SwampFox. The project started as a small site written in Flask backed by a PostgreSQL database, where its only purpose was to display the most used weapons in the clan in PvP (in terms of kill count). It has since evolved into a bigger project with a few more moving parts, and aims to be the home website for my Destiny clan. It's been a ton of fun building this, and I've learned quite a bit in the process and am excited to see where this goes!

# Features
* Clan roster, includes: name of current activity (if the player is online) or the last time the player was in an activity (if the player is offline), Triumph score, highest Power level, and all the Seals that the player has obtained. Updated every 3 minutes.
* Crucible (PvP) weapon stats: this tracks every kill made by every weapon by every player in the clan for every Crucible match they've ever played. These stats can filtered by time ranges and/or weapon types. You can also view a Player's profile to see what weapons they've used most. Updated every 5 minutes.
* Exotic weapon collection: this lists what clan members have which Exotic weapons, and which Exotic weapons have not yet been obtained by any clan member.

# Technologies used

* [Vue.JS](https://vuejs.org/): Javascript frontend framework.
* [nginx](https://www.nginx.com/): Serves frontend and reverse-proxies requests to backend API.
* [Flask](http://flask.pocoo.org/): Backend API written in Python, using Flask-Restplus.
* [PostgreSQL](https://www.postgresql.org/): Database. 
* [Redis](https://redis.io/): Used as first-in-first-out queue when processing new Crucible matches.
* [Docker/Docker-compose](https://www.docker.com/): Each service has its own container: frontend, backend, Redis, and one for the Worker processes. Database is not ran in a container.
* Linux: Container host (CentOS 7) and all container images are based off some flavor of Linux. Mostly Alpine, due to its small footprint.
* [supervisord](http://supervisord.org/): Manages worker processes (Python scripts) in a container that frequently pull new Player data from the Destiny API.
* [GitLab](https://about.gitlab.com/): Version control and CI/CD for the project. 

# How it works

## Roster update

1. Every 3 minutes, a cronjob kicks off a Python script (`%projectroot%/redis_send_player_ids_roster.py`) in the Workers container that publishes all player membershipIDs to a Redis list. Originally, this process was just a script that looped through each player and updated their stats. This clan was several times larger than my previous clan and I was not updating player stats as quick as I wanted to, so that's where Redis came in. Now multiple players can be processed in parallel, and consumption of items from this list can be easily scaled by adding/removing Workers.
2. Several Workers execute BLPOP on the list to consume membershipIDs pull the latest stats from the Destiny API for that player, and send the latest data to the database. Script: (`%projectroot%/stat_collector.py`)
3. Frontend queries the API service for the player data, and will transform some of the data on the client side on each page load. Example: a list of Seals (aka Titles) earned by each player are returned from the API, and the frontend contains computed properties that will transform the Seal name into the corresponding icon for each Seal. 

## Weapon stats update

1. Every 5 minutes, a cronjob kicks off a Python script (`%projectroot%/redis_send_player_ids_pvp.py`) in the Workers container that uses RPUSH to send player membershipIDs to the Redis list (used as a first-in first-out queue of sorts).
2. Several Workers execute BLPOP on the list to grab memembershipIDs and check for new crucible matches played for each character that the player has. In the database, I keep track of the last match processed for each character as well as the last played time for the player; this helps quickly identify new matches played. The Worker then sends new match IDs to a separate Redis list ("matches"). Script: (`%projectroot%/pgcr_consumer.py`)
3. Another set of Workers have executed BLPOP on the matches list. The Worker will then: parse the match for that player's stats, add the new kill count for each weapon to the database (this is tied to the character), and update the character's last match processed in the database. Script: (`%projectroot%/pgcr_consumer.py`)

# The Future

Here are improvemets I want to make in the near future.

* Break up the DestinyAPI class into smaller modules. Example: code related to the Destiny API Manifest should be put into its own module/class.
* Application components are too tightly coupled, as they are defined in one docker-compose file. I should be able to deploy updates to the frontend/backend/Workers separately.
* Tests. Jenkins should run these tests automatically as new code is committed to GitLab.
* Container orchestration, instead of just relying on docker-compose for new deployments.
* Optimize Dockerfiles across all containers to take advantage of build cache.

# Changelog

7/15/2019
* Added tests for API endpoints
* Added Jenkinsfile that describes a simple pipeline for running automated tests when new code is pushed to my self-hosted GitLab server
