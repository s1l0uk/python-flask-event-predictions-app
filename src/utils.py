import pytz

from datetime import datetime


def get_current_time():
    return datetime.utcnow().replace(tzinfo=pytz.utc)


def convert_submit_form_to_dict(form_predictions):
    predictions = []
    for i in range(1, 100):  # hacky solution
        try:
            predictions.append({
                'matchday': int(form_predictions['matchday_{0}'.format(i)]),
                'home_team': form_predictions['home_team_{0}'.format(i)],
                'home_score': form_predictions['home_score_{0}'.format(i)],
                'away_team': form_predictions['away_team_{0}'.format(i)],
                'away_score': form_predictions['away_score_{0}'.format(i)]
            })
        except KeyError:
            pass
    return predictions
