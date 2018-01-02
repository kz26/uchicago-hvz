# University of Chicago Humans versus Zombies

## Description

This is the official repository for the University of Chicago Humans versus Zombies website and game engine.
While this web application has been developed with features specific to our campus and game in mind, you will likely find our
implementation useful should you wish to run your own HvZ game. The reference implementation showcasing all the features
below is live at https://www.uchicagohvz.org. 

This codebase is made available under the terms of the MIT license.

## Gameplay Features
* Real-time game analytics, statistics, individual and squad leaderboards
* Kill logs, geotagging and kill map, powered by Google Maps
* Individual profile pages for players, squads, kills, and missions
* User-definable "Last Words" to be shown to the killer
* Award and Mission system to assign additional points to players and track mission participation
* High-value Target and High-value Dorm system, that awards additional points for killing a specific
player or players from a specific dorm within a specified timeframe

### Player Communication Features
* Kill submission and award/mission code redemption via web form or inbound SMS (powered by Nexmo)
* SMS death notifications via free email-to-SMS gateways
* Separate radio-like chat rooms for humans and zombies (no history and no usernames shown, only timestamps)
* Mailgun webhooks for running all-player chatter, humans-only, and zombies-only mailing lists (see `game/mailing_list.py` and `users/mailing_list.py`)

## Administrative and Technical Features
* Full Bootstrap 3 frontend
* Create and run multiple games, simultaneously if desired
* Player registration flow with squad and dorm selection
* Automatic code generation for players and awards/missions
* Track gun rentals and returns
* Full-featured admin panel

## Requirements

* Linux/Unix-based system
* Django 1.8.x + Python 2.7.x (not tested with Python 3.x) + virtualenv (highly recommended)
* PostgreSQL 9.3+
* Celery 3.1.x + supported task queue (Redis recommended)
* Node.js 0.10.x+ + CoffeeScript for the chat server
* See requirements.txt, package.json files for more requirements

## Customization

**Familiarity with Python and the Django web framework is highly recommended.**

1. For starters, you'll need to edit templates, API keys, Django settings, views, etc. to reflect your organizations' branding and environment. For example, the hosts header in the auth method in `chat/server/server.coffee` will also need to be updated to reflect your site's domain name.  Also make sure to substitute your own Google API key in `templates/includes/google-maps.html`.
2. Create a new user named `uchicagohvz`.
3. Create a virtualenv and install dependencies from requirements.txt.
4. Create an `environment` file that will contain things like secret keys, credentials, etc. Check `local_settings.py` and `production_settings.py` to get an idea of what this file needs to contain. The environment file can be used with systemd, as demonstrated with the provided sample systemd configs.
5. Implement a Django authentication backend specific to your organization/deployment. The reference implementation here
contains a backend that talks to UChicago's LDAP server and allows us to directly retrieve player names, usernames,
and major, in addition to authenticating user credentials during login. Ideally, your authentication backend will be able to do all of these
tasks; otherwise, you will need to fall back to a traditional email registration/activation setup (we have also implemented a basic registration flow to allow players without university credentials to register.)
6. The `users` module contains UChicago-specific Sympa mailing list management hooks in `models.py`; you will want to modify this or remove it altogether.
7. Don't forget to set up a Nexmo SMS account if you wish to enable kill/code redemption via inbound SMS.

