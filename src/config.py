import os
import random
import string
from datetime import timedelta
from configparser import ConfigParser


def read_config(config_path):
    config = ConfigParser()
    # TODO: Expand to other types of config
    config_parser(config, config_path)
    return config


def config_parser(config, config_path):
    config.read(config_path)
    return config


def app_config(app, config):
    logins = []
    for section in config.sections():
        if '_login' in section:
            name = section.replace('_login', '')
            logins.append(name)
            upper_name = name.upper()
            client = {}
            for key in config[section]:
                client[upper_name + "_" + key.upper()] = config.get(section, key)
            for d in required_fields():
                if not upper_name + "_" + d.upper() in client.keys():
                    try:
                        client[upper_name + "_" + d.upper()] = os.environ[upper_name + "_" + d.upper()]
                    except KeyError:
                        quit('Cannot find ' + upper_name + "_" + d.upper())
            app.config.update(**client)
    app.config.update(
        OAUTH_SOURCES=logins,
        SECRET_KEY=config.get('flask', 'secret_key',
                              fallback=os.environ.get(
                                  'FLASK_SECRET_KEY',
                                  ''.join(
                                      random.choice(
                                          string.ascii_uppercase + string.ascii_lowercase + string.digits
                                      ) for _ in range(16)
                                  )
                              )
                              ),
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=20),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        WHITELISTED_DOMAINS=os.environ.get('whitelisted_domains', config.get('flask', 'whitelisted_domains', fallback='*')),
        SQLALCHEMY_TRACK_MODIFICATIONS=config.get('db', 'sqlalchemy_track_modifications', fallback=False),
        SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI', config.get('db', 'sqlalchemy_db_url', fallback=None)),
        EVENT_ID=os.environ.get('EVENT_ID', config.get('event', 'competition', fallback=None)),
        EVENT_API_KEY=os.environ.get('EVENT_API_KEY', config.get('event', 'api_key', fallback=None)),
        CORPORATE_SPONSER=os.environ.get('CORPORATE_SPONSER', config.get('flask', 'corporate_sponser', fallback=None)),
        CORPORATE_SPONSER_LOGO=os.environ.get('CORPORATE_SPONSER_LOGO', config.get('flask', 'corporate_sponser_logo', fallback=None)),
        APP_CSS=os.environ.get('APP_CSS', config.get('flask', 'css_file', fallback="business-frontpage.css"))
    )
    return app


def required_fields():
    return [
        'client_id',
        'client_secret',
        'client_kwargs',
        'userinfo_endpoint',
        'authorize_url',
        'access_token_url',
        'api_base_url',
        'jwks_uri'
    ]
