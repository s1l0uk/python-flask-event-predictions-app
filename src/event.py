import requests


class FootballClient(object):

    def __init__(self, api_key, competition):
        self.base_endpoint = 'https://api.football-data.org/v4/competitions'
        self.competition = competition
        self.requests = requests.Session()
        self.requests.headers.update({'X-Auth-Token': api_key})
        self._all_teams = None
        self._all_matches = None
        self._event = None

    def get_all_fixtures(self):
        self.get_all_matches()
        return self._all_matches

    def get_event(self):
        if self._event is None:
            response = self.requests.get(
                '{0}/'.format(
                    self.base_endpoint
                )
            )
            response.raise_for_status()
            data = response.json()
            for c in data['competitions']:
                match = [c['id'], c['name'], c['code']]
                if self.competition in match:
                    self._event = c
            return self._event

    def get_all_teams(self):
        if self._all_teams is None:
            response = self.requests.get(
                '{0}/{1}/teams'.format(
                    self.base_endpoint, self.competition
                )
            )
            response.raise_for_status()
            data = response.json()
            self._all_teams = [
                (team['name'], team['crest']) for team in data['teams']
            ]
        return self._all_teams

    def get_all_matches(self):
        if self._all_matches is None:
            response = self.requests.get(
                '{0}/{1}/matches'.format(
                    self.base_endpoint, self.competition
                )
            )
            response.raise_for_status()
            self._all_matches = response.json()['matches']
        return self._all_matches

    def get_results(self):
        response = self.requests.get(
            '{0}/{1}/matches'.format(
                self.base_endpoint, self.competition
            )
        )
        response.raise_for_status()
        results = {}
        for fixture in response.json()['matches']:
            if (
                fixture['score']['fullTime']['home'] is not None and
                fixture['score']['fullTime']['away'] is not None
            ):
                game = '{}_{}_{}'.format(
                    fixture['matchday'],
                    fixture['homeTeam']['name'],
                    fixture['awayTeam']['name']
                )
                if fixture['score'].get('extraTime'):
                    score = {
                        'home_score': fixture['score']['extraTime']['home'],  # noqa
                        'away_score': fixture['score']['extraTime']['away']  # noqa
                    }
                else:
                    score = {
                        'home_score': fixture['score']['fullTime']['home'],
                        'away_score': fixture['score']['fullTime']['away']
                    }
                results[game] = score
        return results

    def check_predictions_validity(self, predictions):
        matches = self.get_all_matches()

        def find_fixture(matchday, home_team, away_team):
            games = [
                fixture for fixture in matches
                if fixture['matchday'] == matchday and
                fixture['homeTeam']['name'] == home_team and
                fixture['awayTeam']['name'] == away_team
            ]
            if len(games) != 1:
                raise Exception(
                    'Looks like you tried to predict the score for a game '
                    'that doesn\'t exist.'
                )
            return games[0]

        for prediction in predictions:
            fixture = find_fixture(
                prediction['matchday'],
                prediction['home_team'],
                prediction['away_team']
            )
            if fixture['status'] not in ['SCHEDULED', 'TIMED']:
                raise Exception(
                    'You can\'t set a prediction for a game that isn\'t in a '
                    'scheduled state.'
                )

        return True
