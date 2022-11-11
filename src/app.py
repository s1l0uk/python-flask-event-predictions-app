#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dateutil.parser import parser as parse_date
from flask import Flask, session, jsonify, url_for, redirect, request, \
    render_template, flash
from config import read_config, app_config
from db import DB
from oauth import register_oauth_clients
from event import FootballClient
from utils import get_current_time, convert_submit_form_to_dict
from werkzeug.middleware.proxy_fix import ProxyFix

config = read_config('./config/config.cfg')
app = app_config(Flask(__name__), config)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)


# Set up Sports API Client
event = FootballClient(
    app.config.get("EVENT_API_KEY"),
    app.config.get("EVENT_ID")
)
event_info = event.get_event()
event_info["sponser"] = {
    "sponser_name": app.config.get("CORPORATE_SPONSER",""),
    "logo": app.config.get("CORPORATE_SPONSER_LOGO", "")

}

# Set up DB
db = DB(app, event.get_all_teams())

# Set up OAuth
oauth, oauth_clients = register_oauth_clients(app)


@app.template_filter('strftime')
def strftime(date_time):
    date_time_object = parse_date().parse(date_time)
    return date_time_object.strftime('%a %d %B %Y - %H:%M UTC')


@app.template_filter('convert_to_datetime')
def convert_to_datetime(date_time):
    return parse_date().parse(date_time)


@app.errorhandler(Exception)
def error(error):
    return jsonify(error=str(error)), 500


@app.route('/<provider>/login')
def login(provider):
    redirect_uri = url_for('authorize', provider=provider, _external=True)
    return oauth_clients['google'].authorize_redirect(redirect_uri)


@app.route('/<provider>/login/authorize')
def authorize(provider):
    token = oauth_clients[provider].authorize_access_token()
    session['access_token'] = token, ''
    user_info = oauth_clients[provider].userinfo()
    try:
        db.add_user(
            app.config.get("WHITELISTED_DOMAINS", "*"), user_info, token
        )
    except Exception as e:
        return jsonify(error='Forbidden'), 403
    session.permanent = True
    session['sub'] = user_info['sub']
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/status')
def status():
    return jsonify(status='OK')


@app.route('/')
def index():
    if session.get('sub'):
        return redirect(url_for('home'))
    return render_template(
        'index.html',
        css=app.config.get('APP_CSS'),
        event=event_info,
        sso_login_urls=[
            {
                "name": x.capitalize(),
                "url": url_for('login', provider=x)
            } for x in oauth_clients
        ],
        user_count=db.get_user_count()
    )


@app.route('/home')
def home():
    return render_template(
        'home.html',
        css=app.config.get('APP_CSS'),
        event=event_info,
        user=db.get_user(session['sub']).to_json(),
        picture=oauth_clients['google'].userinfo(token=session['access_token'][0])['picture'],
        fixtures=[x for x in event.get_all_matches() if x['matchday'] is not None],
        points=db.get_points_for_user(session['sub']),
        current_time=get_current_time()
    )


@app.route('/home/submit', methods=['POST'])
def submit():
    user = db.get_user(session['sub'])
    predictions = convert_submit_form_to_dict(request.form)
    try:
        event.check_predictions_validity(predictions)
        db.add_predictions(user, predictions)
        flash('Your predictions were successfully saved!', 'info')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('home'))


@app.route('/user/<int:user_id>')
def user(user_id):
    other_user = db.get_user_by_id(user_id)
    return render_template(
        'home.html',
        css=app.config.get('APP_CSS'),
        event=event_info,
        user=db.get_user(session['sub']).to_json(),
        picture=oauth_clients['google'].userinfo(token=session['access_token'][0])['picture'],
        fixtures=[x for x in event.get_all_matches() if x['matchday'] is not None],
        points=db.get_points_for_user(other_user.sub),
        other_user=other_user.to_json(),
        current_time=get_current_time()
    )


@app.route('/sweepstakes')
def sweepstakes():
    return render_template(
        'sweepstakes.html',
        css=app.config.get('APP_CSS'),
        event=event_info,
        user=db.get_user(session['sub']).to_json(),
        picture=oauth_clients['google'].userinfo(token=session['access_token'][0])['picture'],
        allocations=db.get_team_allocations()
    )


@app.route('/predictions')
def predictions():
    return render_template(
        'predictions.html',
        css=app.config.get('APP_CSS'),
        event=event_info,
        user=db.get_user(session['sub']).to_json(),
        picture=oauth_clients['google'].userinfo(token=session['access_token'][0])['picture'],
        leaderboard=db.get_predictions_leaderboard()
    )


if __name__ == '__main__':
    app.run(port=8000, debug=True)
