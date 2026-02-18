"""Background job scheduler for periodic tasks."""

import random
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from website.extensions import db
from website.services.user import UserService

BATCH_SIZE = 50
FREQUENCY = 5
INACTIVE_CHECK_BATCH_SIZE = 10


def refresh_user_profiles(app, batch_size=BATCH_SIZE):
    """Refresh a random batch of active user profiles from Discord.

    Users marked as inactive (not_player_as_of is set) are excluded.
    When a 404 is encountered, the user is marked inactive.

    Queries only user IDs first to avoid loading all ORM objects
    (and triggering init_on_load for every active user).

    Args:
        app: Flask application instance for context.
        batch_size: Number of users to refresh per run.
    """
    with app.app_context():
        service = UserService()
        user_ids = service.get_active_user_ids()
        if not user_ids:
            return

        sample_ids = random.sample(user_ids, min(batch_size, len(user_ids)))
        to_refresh = service.get_by_ids(sample_ids)
        for user in to_refresh:
            try:
                profile = service.get_user_profile(user.id, force_refresh=True)
                if profile.get("not_found"):
                    user.not_player_as_of = datetime.now(timezone.utc)
                    app.logger.info(f"[Scheduler] Marked user {user.id} as inactive (404)")
                else:
                    user.name = profile["name"]
                    user.avatar = profile["avatar"]
                    if profile.get("username"):
                        user.username = profile["username"]
            except Exception as e:
                app.logger.warning(f"[{datetime.now()}] Failed to refresh {user.id}: {e}")

        db.session.commit()
        app.logger.info(f"[Scheduler] Refreshed {len(to_refresh)} users at {datetime.now()}")


def check_inactive_users(app, batch_size=INACTIVE_CHECK_BATCH_SIZE):
    """Re-check a batch of inactive users to see if they have rejoined.

    If the Discord API returns a valid profile, the not_player_as_of
    flag is cleared.

    Queries only user IDs first to avoid loading all ORM objects
    (and triggering init_on_load for every inactive user).

    Args:
        app: Flask application instance for context.
        batch_size: Number of inactive users to check per run.
    """
    with app.app_context():
        service = UserService()
        inactive_ids = service.get_inactive_user_ids()
        if not inactive_ids:
            return

        sample_ids = random.sample(inactive_ids, min(batch_size, len(inactive_ids)))
        to_check = service.get_by_ids(sample_ids)
        reactivated = 0
        for user in to_check:
            try:
                profile = service.get_user_profile(user.id, force_refresh=True)
                if not profile.get("not_found"):
                    user.not_player_as_of = None
                    user.name = profile["name"]
                    user.avatar = profile["avatar"]
                    if profile.get("username"):
                        user.username = profile["username"]
                    reactivated += 1
                    app.logger.info(
                        f"[Scheduler] User {user.id} has rejoined, clearing inactive flag"
                    )
            except Exception as e:
                app.logger.warning(f"[Scheduler] Failed to re-check inactive user {user.id}: {e}")

        db.session.commit()
        app.logger.info(
            f"[Scheduler] Checked {len(to_check)} inactive users, "
            f"reactivated {reactivated} at {datetime.now()}"
        )


def start_scheduler(app):
    """Initialize and start the APScheduler background scheduler.

    Args:
        app: Flask application instance.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: refresh_user_profiles(app),
        trigger="interval",
        minutes=FREQUENCY,
        id="refresh_user_profiles",
        replace_existing=True,
    )
    scheduler.add_job(
        func=lambda: check_inactive_users(app),
        trigger="interval",
        hours=24,
        id="check_inactive_users",
        replace_existing=True,
    )
    scheduler.start()

    # Shut down the scheduler when Flask stops
    import atexit

    atexit.register(lambda: scheduler.shutdown())
