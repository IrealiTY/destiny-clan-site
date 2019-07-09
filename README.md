# Overview

A Destiny 2 stat site made for my clan, SwampFox.

# Features
* Clan roster, includes: name of current activity (if the player is online) or the last time the player was in an activity (if the player is offline), Triumph score, highest Power level, and all the Seals that the player has obtained. Updated every 3 minutes.
* Crucible (PvP) weapon stats: this tracks every kill made by every weapon by every player in the clan for every Crucible match they've ever played. These stats can filtered by time ranges and/or weapon types. I thought it'd be interesting to see which weapons got the most use in the clan. Updated every 5 minutes.

# Components

* Frontend: [Vue.JS](https://vuejs.org/)
* Backend: Python Flask API
* Database: PostgreSQL
* Message queue: Redis
* Workers: a small set of Python workers that are responsible for updating Player stats.
