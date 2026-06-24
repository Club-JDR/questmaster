"""Background job scheduler for periodic tasks."""

import random
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from website.services.user import UserService

BATCH_SIZE = 50
FREQUENCY = 5
INACTIVE_CHECK_BATCH_SIZE = 10
ROLE_MONITOR_FREQUENCY_HOURS = 12


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
        refreshed = 0
        for user_id in sample_ids:
            try:
                profile = service.get_user_profile(user_id, force_refresh=True)
                if profile.get("not_found"):
                    service.mark_inactive(user_id)
                    app.logger.info(f"[Scheduler] Marked user {user_id} as inactive (404)")
                elif profile.get("error"):
                    # Transient Discord failure (5xx, rate limit, network): leave the
                    # existing profile untouched rather than clobbering it with "Inconnu".
                    app.logger.warning(
                        f"[Scheduler] Skipping {user_id}: transient profile fetch error"
                    )
                else:
                    service.persist_profile(user_id, profile)
                    refreshed += 1
            except Exception as e:
                app.logger.warning(f"[{datetime.now()}] Failed to refresh {user_id}: {e}")

        app.logger.info(f"[Scheduler] Refreshed {refreshed} users at {datetime.now()}")


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
        reactivated = 0
        for user_id in sample_ids:
            try:
                profile = service.get_user_profile(user_id, force_refresh=True)
                if profile.get("error"):
                    # Transient failure (not a 404): cannot conclude the user rejoined.
                    continue
                if not profile.get("not_found"):
                    service.persist_profile(user_id, profile, reactivate=True)
                    reactivated += 1
                    app.logger.info(
                        f"[Scheduler] User {user_id} has rejoined, clearing inactive flag"
                    )
            except Exception as e:
                app.logger.warning(f"[Scheduler] Failed to re-check inactive user {user_id}: {e}")

        app.logger.info(
            f"[Scheduler] Checked {len(sample_ids)} inactive users, "
            f"reactivated {reactivated} at {datetime.now()}"
        )


def monitor_role_count(app):
    """Auto-enable direct channel permissions when the guild nears its role limit.

    A Discord guild is hard-capped at 250 roles. When the current role count reaches
    the admin-configured threshold, this switches new games to direct per-player
    channel permissions so no further roles are consumed. It never disables the
    setting automatically; an admin can turn it back off manually.

    Args:
        app: Flask application instance for context.
    """
    from website.services.discord import DiscordService
    from website.services.setting import SettingsService

    with app.app_context():
        settings = SettingsService()
        if settings.is_direct_permissions_enabled():
            return

        try:
            count = DiscordService().count_roles()
        except Exception as e:
            app.logger.warning(f"[Scheduler] Could not fetch role count: {e}")
            return

        threshold = settings.get_role_auto_threshold()
        if count >= threshold:
            settings.set_direct_permissions(True)
            app.logger.info(
                f"[Scheduler] Role count {count} >= threshold {threshold}; "
                "direct channel permissions auto-enabled."
            )
        else:
            app.logger.info(
                f"[Scheduler] Role count {count} below threshold {threshold}; no change."
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
    scheduler.add_job(
        func=lambda: monitor_role_count(app),
        trigger="interval",
        hours=ROLE_MONITOR_FREQUENCY_HOURS,
        id="monitor_role_count",
        replace_existing=True,
    )
    scheduler.start()

    # Shut down the scheduler when Flask stops
    import atexit

    atexit.register(lambda: scheduler.shutdown())
