import random

from datetime import datetime
from collections import OrderedDict
from sqlalchemy import desc

from models import db, User, Team, Result, Prediction


class DB(object):

    def __init__(self, app, teams):
        self.initialise_database(app, teams)

    def initialise_database(self, app, teams):
        with app.app_context():
            db.init_app(app)
            db.create_all()
            db_teams = [
                Team(name=team, crest_url=crest_url)
                for team, crest_url in teams
            ]
            db.session.add_all(db_teams)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                pass  # DB already initiased

    def get_users(self):
        return User.query.all()

    def get_user(self, sub):
        return User.query.filter_by(sub=sub).one()

    def get_user_by_id(self, id):
        return User.query.filter_by(id=id).one()

    def get_user_count(self):
        return User.query.count()

    def add_user(self, valid_domains, user_info, token):
        if (
            valid_domains != '*' and
            user_info.get('hd') not in valid_domains.split(',')
        ):
            raise Exception('Invalid email domain')
        user = User.query.filter_by(sub=user_info['sub']).first()
        if user is None:
            user = User(
                sub=user_info['sub'],
                email=user_info['email'],
                name=user_info['name'],
                allocated_team_id=self.allocate_team().id,
                token_type=token['token_type'],
                access_token=token['access_token'],
                refresh_token=token.get('refresh_token'),
                expires_at=(
                    int(datetime.utcnow().timestamp()) + token['expires_in']
                )
            )
        else:
            user.token_type = token['token_type']
            user.access_token = token['access_token']
            user.expires_at = (
                int(datetime.utcnow().timestamp()) + token['expires_in']
            )
            if token.get('refresh_token'):
                user.refresh_token = token['refresh_token']
        db.session.add(user)
        db.session.commit()
        return user

    def refresh_user_token(self, sub, token):
        user = User.query.filter_by(sub=sub).one()
        user.token_type = token['token_type']
        user.access_token = token['access_token']
        user.expires_at = (
            int(datetime.utcnow().timestamp()) + token['expires_in']
        )
        if token.get('refresh_token'):
            user.refresh_token = token['refresh_token']
        db.session.add(user)
        db.session.commit()
        return user.to_token()

    def allocate_team(self):
        teams = Team.query.all()
        unallocated_teams = []
        i = 0
        while unallocated_teams == []:
            unallocated_teams = [
                team for team in teams if len(team.allocated_users) <= i
            ]
            i += 1
        return random.choice(unallocated_teams)

    def get_user_token(self, sub):
        user = User.query.filter_by(sub=sub).one()
        return user.to_token()

    def get_points_for_user(self, sub):
        predictions = self.get_user(sub).to_json()['predictions']

        # Cater for fact that results table might not exist
        try:
            results = Result.query.all()
        except Exception:
            return {}

        user_points = {}

        for result in results:
            game = result.get_key()
            if game in predictions:
                score = result.get_value()
                score_str = '{home_score} - {away_score}'.format(**score)
                if (
                    score['home_score'] == predictions[game]['home_score'] and
                    score['away_score'] == predictions[game]['away_score']
                ):
                    user_points[game] = {
                        'result': score_str,
                        'points': 3
                    }
                elif (
                    score['home_score'] == score['away_score'] and
                    predictions[game]['home_score'] == predictions[game]['away_score']  # noqa
                ):
                    user_points[game] = {
                        'result': score_str,
                        'points': 1
                    }
                elif (
                    score['home_score'] > score['away_score'] and
                    predictions[game]['home_score'] > predictions[game]['away_score']  # noqa
                ):
                    user_points[game] = {
                        'result': score_str,
                        'points': 1
                    }
                elif (
                    score['home_score'] < score['away_score'] and
                    predictions[game]['home_score'] < predictions[game]['away_score']  # noqa
                ):
                    user_points[game] = {
                        'result': score_str,
                        'points': 1
                    }
                else:
                    user_points[game] = {
                        'result': score_str,
                        'points': 0
                    }

        return user_points

    def add_predictions(self, user, predictions):
        for prediction in predictions:
            if prediction['home_score'] != '' \
               and prediction['away_score'] != '':
                try:
                    db_prediction = Prediction.query.filter_by(
                        user_id=user.id,
                        matchday=prediction['matchday'],
                        home_team=prediction['home_team'],
                        away_team=prediction['away_team']
                    ).first()

                    if db_prediction is None:
                        db_prediction = Prediction(
                            matchday=prediction['matchday'],
                            home_team=prediction['home_team'],
                            home_score=prediction['home_score'],
                            away_team=prediction['away_team'],
                            away_score=prediction['away_score']
                        )
                        db.session.add(db_prediction)
                        user.predictions.append(db_prediction)
                    else:
                        db_prediction.home_score = prediction['home_score']
                        db_prediction.away_score = prediction['away_score']
                except Exception as e:
                    db.session.rollback()
                    raise
        db.session.commit()
        return True

    def get_team_allocations(self):
        all_teams = Team.query.all()
        return {
            team.name: ", ".join([user.name for user in team.allocated_users])
            for team in all_teams
        }

    def get_predictions_leaderboard(self):
        all_users = User.query.order_by(desc(User.points)).all()
        leaderboard = OrderedDict()
        for user in all_users:
            leaderboard[user.name] = {
                "id": user.id,
                "points": user.points
            }
        return leaderboard
