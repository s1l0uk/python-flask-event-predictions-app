#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from functools import wraps
from authlib.integrations.flask_client import OAuth
from flask import session, url_for, request, redirect


def register_oauth_clients(app):
    oauth = OAuth()
    oauth.init_app(app)
    clients = {}
    for client in app.config.get("OAUTH_SOURCES"):
        scoped_config = {}
        for c in app.config.keys():
            if client.upper() in c:
                scoped_config[
                    c.lower().replace(client + "_", "")
                ] = app.config[c]
        clients[client] = register_client(oauth, client, scoped_config)
    return oauth, clients


def register_client(oauth, name, config):
    try:
        config["client_kwargs"] = json.loads(config["client_kwargs"])
    except KeyError:
        pass
    return oauth.register(name, **config)


def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('sub'):
            url = url_for('login', next=request.path)
            return redirect(url)
        return f(*args, **kwargs)
    return decorated
