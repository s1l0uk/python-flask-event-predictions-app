import logging
import os
from pprint import pprint

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import read_config
from event import FootballClient
from models import User, Result


def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger


def get_db_session(db_url):
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def update_results(session, results):
    for game in results:
        try:
            result = session.query(Result).filter_by(
                matchday=game.split("_")[0],
                home_team=game.split("_")[1],
                away_team=game.split("_")[2]
            ).first()
            if not result:
                result = Result(
                    matchday=game.split("_")[0],
                    home_team=game.split("_")[1],
                    home_score=results[game]["home_score"],
                    away_team=game.split("_")[2],
                    away_score=results[game]["away_score"]
                )
            else:
                result.home_score = results[game]["home_score"]
                result.away_score = results[game]["away_score"]
            session.add(result)
            session.commit()
        except Exception:
            session.rollback()


def calculate_points(predictions, results):
    points = 0
    for prediction in predictions:
        game = prediction.get_key()
        if game in results:
            predicted_score = prediction.get_value()
            if (
                predicted_score["home_score"] == results[game]["home_score"] and  # noqa
                predicted_score["away_score"] == results[game]["away_score"]
            ):
                points += 3
            elif (
                predicted_score["home_score"] == predicted_score["away_score"] and  # noqa
                results[game]["home_score"] == results[game]["away_score"]
            ):
                points += 1
            elif (
                predicted_score["home_score"] > predicted_score["away_score"] and  # noqa
                results[game]["home_score"] > results[game]["away_score"]
            ):
                points += 1
            elif (
                predicted_score["home_score"] < predicted_score["away_score"] and  # noqa
                results[game]["home_score"] < results[game]["away_score"]
            ):
                points += 1
    return points


def lambda_handler(event, context):
    logger = setup_logger()
    config = read_config("src/config/config.cfg")
    session = get_db_session(config.get("db", "sqlalchemy_db_url", fallback=os.environ['SQLALCHEMY_DATABASE_URI']))
    football_client = FootballClient(
        config.get("event", "api_key", fallback=os.environ['EVENT_API_KEY']),
        config.get("event", "competition", fallback=os.environ['EVENT_ID'])
    )

    # Get game results
    results = football_client.get_results()
    logger.warn("Results are:")
    pprint(results)

    # Update results
    update_results(session, results)

    # Update points
    users = session.query(User).all()
    for user in users:
        logger.warn("Updating points for {}".format(user.name))
        user.points = calculate_points(user.predictions, results)
    try:
        logger.warn("Committing points update")
        session.commit()
        logger.warn("Success!")
    except Exception as e:
        session.rollback()
        logger.exception(e)
    return 0


if __name__ == "__main__":
    lambda_handler(None, None)
