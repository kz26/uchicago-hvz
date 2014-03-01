# University of Chicago Humans versus Zombies

## Description

This is the official repository for the University of Chicago (UChicago) Humans versus Zombies website and game engine.
While this game engine was developed with features specific to our campus and game in mind, you will likely find our
implementation useful should you wish to run your own HvZ game. The reference implementation showcasing all the features
below is viewable at https://www.uchicagohvz.org. 

This codebase is made available under the terms of the MIT license.

## Features

* Create and run multiple games, simultaneously if desired
* Pre-register players, and record players' majors and dorms
* Automatic code generation for players and awards/missions
* Real-time stats - game analytics, individual and squad leaderboards
* Kills can be annotated with geotags (powered by Google Maps) and notes
* Kill submission and award/mission code redemption via web form and inbound Nexmo SMS
* SMS death notifications (uses free email-to-SMS gateways)
* Player squad support
* Individual profile pages for players, squads, and kills
* Separate radio-like chat rooms for humans and zombies (no history and no usernames shown, only timestamps)
* "Award" system for assigning/deducting points to players (useful for missions, minigames, etc.)
* High-value Target and High-value Dorm system, which awards additional points for killing a specific
player or players from a specific dorm within a specified timeframe
* Track gun rentals and returns
* Full Bootstrap 3.1 frontend
* Full-featured admin panel, courtesy of Django

## Requirements

* Django 1.6.x + Python 2.7.x (not tested with Python 3.x)
* Django-supported database backend (PostgreSQL recommended)
* Celery 3.1.x + supported task queue (Redis recommended)
* Node.js 0.10.x + CoffeeScript for the chat server
* See requirements.txt, package.json files for more requirements

## Customization

**Familiarity with Python and the Django web framework is highly recommended.**

1. For starters, you'll need to edit the templates and Django settings to reflect your organizations' branding and environment.
The hosts header in the auth method in `chat/server/server.coffee` will also need to be updated to reflect your site's domain name.
2. Create a `secrets.py` file in the same directory as `local_settings.py`. At minimum this file should
contain a `SECRET_KEY`. Also make sure to substitute your own Google API key in `templates/includes/google-maps.html`.
3. Implement a Django authentication backend specific to your organization/deployment. Our reference implementation's
primary authentication backend talks to UChicago's LDAP server and allows us to directly retrieve player names, usernames,
and major, in addition to authenticating user credentials during login. Ideally, your authentication backend will be able to do all of these
tasks; otherwise, you will need to fall back to a traditional email registration/activation setup (code not included.)
4. The users module contains email listhost management specific to UChicago; you will want to modify this or remove it altogether.
5. Don't forget to set up a Nexmo SMS account if you wish to enable kill/code redemption via inbound SMS.

