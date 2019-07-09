# Overview

A Destiny 2 stat site made for my clan, SwampFox. The project started as a small site written in Flask backed by a PostgreSQL database, where its only purpose was to display what weapons were most popular in PvP (in terms of kill count). It has since evolved into a bigger project with a few more moving parts, and aims to be a landing page for my clan's Destiny stats.

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
* [Docker/Docker-compose](https://www.docker.com/): All services are ran in containers, and defined by docker-compose
* [supervisord](http://supervisord.org/): Manages worker processes (Python scripts) in a container that frequently pull new Player data from the Destiny API
* [Jenkins](https://jenkins.io/): Builds and deploys the project

# Development

# Deployment
