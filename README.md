# Overview

The application can be viewed here: http://destiny.thebrobotic.com/ (design is a work in progress, right now I'm focusing on functionality first)

A Destiny 2 stat site made for my clan, SwampFox. The project started as a small site written in Flask backed by a PostgreSQL database, where its only purpose was to display what weapons were most popular in PvP (in terms of kill count). It has since evolved into a bigger project with a few more moving parts, and aims to be the home website for my Destiny clan. It's been a ton of fun building this, and I've learned quite a bit in the process and am excited to see where this goes!

# Features
* Clan roster, includes: name of current activity (if the player is online) or the last time the player was in an activity (if the player is offline), Triumph score, highest Power level, and all the Seals that the player has obtained. Updated every 3 minutes.
* Crucible (PvP) weapon stats: this tracks every kill made by every weapon by every player in the clan for every Crucible match they've ever played. These stats can filtered by time ranges and/or weapon types. Updated every 5 minutes.
* Exotic weapon collection: this lists what clan members have which Exotic weapons, and which Exotic weapons have not yet been obtained by any clan member.

# Technologies used

* [Vue.JS](https://vuejs.org/): Javascript frontend framework
* [nginx](https://www.nginx.com/): Serves frontend and reverse-proxies requests to backend API
* [Flask](http://flask.pocoo.org/): Backend API written in Python
* [PostgreSQL](https://www.postgresql.org/): Database
* [Redis](https://redis.io/): Message queue
* [Docker/Docker-compose](https://www.docker.com/): All services are ran in containers: frontend, backend API, 
* [supervisord](http://supervisord.org/): Manages worker processes (Python scripts) in a container that frequently pull new Player data from the Destiny API
* [Jenkins](https://jenkins.io/): Builds and deploys the project
* [GitLab](https://about.gitlab.com/): Version control for the project

# How it works

## Roster update

1. Every 3 minutes, a cronjob kicks off a Python script in the Workers container that sends all player membershipId's to the Redis message queue.
2. Workers will pop player memembershipId's from the queue and pull the latest stats from the Destiny API for that player, and send the latest data to the database.
3. Frontend queries the backend API for the player data, and will transform some of the data on the client side on each page load. Example: a list of Seals earned by the Player are returned from the API, and the frontend will loop through each Seal for each player and display the corresponding image for that seal. 


# Deployment

# The Future

Here are improvemets I want to make in the near future.

* Break up the DestinyAPI class into smaller modules. Example: code related to the Destiny API Manifest should be put into its own module/class. 
* Tests. Jenkins should run these tests automatically as new code is committed to GitLab.
* Container orchestration, instead of just relying on docker-compose for new deployments.
