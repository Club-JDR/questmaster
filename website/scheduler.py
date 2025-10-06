from datetime import datetime
import random
from website.models.user import User, get_user_profile
from website.extensions import db
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app


BATCH_SIZE = 50
FREQUENCY = 5


def refresh_user_profiles(app, batch_size=BATCH_SIZE):
    """
    Refresh a random batch of user profiles in Redis (and optionally DB).
    """
    with app.app_context():
        users = User.query.all()
        if not users:
            return

        to_refresh = random.sample(users, min(batch_size, len(users)))
        for user in to_refresh:
            try:
                profile = get_user_profile(user.id, force_refresh=True)
                user.name = profile["name"]
                user.avatar = profile["avatar"]
            except Exception as e:
                app.logger.warning(
                    f"[{datetime.now()}] Failed to refresh {user.id}: {e}"
                )

        db.session.commit()
        app.logger.info(
            f"[Scheduler] Refreshed {len(to_refresh)} users at {datetime.now()}"
        )


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: refresh_user_profiles(app),
        trigger="interval",
        minutes=FREQUENCY,
        id="refresh_user_profiles",
        replace_existing=True,
    )
    scheduler.start()

    # Shut down the scheduler when Flask stops
    import atexit

    atexit.register(lambda: scheduler.shutdown())
