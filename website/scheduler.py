"""Background job scheduler for periodic tasks."""

import random
from datetime import datetime, timedelta, timezone

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from website.services.user import UserService

FREQUENCY = 5
INACTIVE_CHECK_BATCH_SIZE = 10
ROLE_MONITOR_FREQUENCY_HOURS = 12
# Per-fire random drift (seconds) applied to the long-running jobs so repeated
# runs do not realign on the same instant. ±1h.
DAILY_JOB_JITTER = 3600
# Largest random delay (minutes) before a long job's *first* run, so the daily
# jobs do not all fire together ~24h after startup.
DAILY_JOB_START_SPREAD = 30


def refresh_user_profiles(app, batch_size=None):
    """Refresh a random batch of active user profiles from Discord.

    Users marked as inactive (not_player_as_of is set) are excluded.
    When a 404 is encountered, the user is marked inactive.

    Queries only user IDs first to avoid loading all ORM objects
    (and triggering init_on_load for every active user).

    Args:
        app: Flask application instance for context.
        batch_size: Number of users to refresh per run. When ``None`` (the
            scheduled default), the admin-configured batch size is resolved at
            run time so changes take effect without restarting the scheduler.
    """
    with app.app_context():
        service = UserService()
        if batch_size is None:
            from website.services.setting import SettingsService

            batch_size = SettingsService().get_profile_refresh_batch_size()
        user_ids = service.get_active_user_ids()
        if not user_ids:
            app.logger.info("[Scheduler] No active users to refresh")
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
            app.logger.info("[Scheduler] No inactive users to re-check")
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
            app.logger.info(
                "[Scheduler] Direct permissions already enabled; skipping role-count check"
            )
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


def monitor_category_capacity(app):
    """Daily: reconcile category sizes and auto-provision near-full categories.

    Corrects each tracked category's channel count from Discord, then, for every
    game type, creates a fresh category when all of that type's categories are at
    or above the admin-configured auto-provision threshold.

    Args:
        app: Flask application instance for context.
    """
    from config.constants import GAME_TYPES
    from website.services.channel import ChannelService
    from website.services.discord import DiscordService

    with app.app_context():
        discord = DiscordService()
        channels = ChannelService()
        try:
            channels.reconcile_sizes(discord)
            for game_type in GAME_TYPES:
                created = channels.auto_provision_if_full(discord, game_type)
                if created:
                    app.logger.info(
                        f"[Scheduler] Auto-provisioned category {created.id} "
                        f"for type '{game_type}'."
                    )
        except Exception as e:
            app.logger.warning(f"[Scheduler] Category capacity check failed: {e}")


def prune_app_logs(app):
    """Daily: delete application log rows older than the retention window.

    The retention window is ``LOG_RETENTION_DAYS`` (env ``QM_LOG_RETENTION_DAYS``,
    default 30 days).

    Args:
        app: Flask application instance for context.
    """
    from website.services.app_log import AppLogService

    with app.app_context():
        try:
            deleted = AppLogService().prune(app.config["LOG_RETENTION_DAYS"])
            app.logger.info(f"[Scheduler] Pruned {deleted} application log rows")
        except Exception as e:
            app.logger.warning(f"[Scheduler] Application log pruning failed: {e}")


def start_scheduler(app):
    """Initialize and start the APScheduler background scheduler.

    Args:
        app: Flask application instance.
    """
    # A single worker serialises every job, so no two jobs ever run in parallel;
    # coalesce + max_instances=1 also stop a job from stacking up on itself if a
    # run is delayed.
    scheduler = BackgroundScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=1)},
        job_defaults={"coalesce": True, "max_instances": 1},
    )

    # Passing the function and ``args`` (instead of a ``lambda``) keeps the job's
    # real name in APScheduler's logs rather than "<lambda>".
    scheduler.add_job(
        func=refresh_user_profiles,
        args=[app],
        trigger="interval",
        minutes=FREQUENCY,
        id="refresh_user_profiles",
        name="refresh_user_profiles",
        replace_existing=True,
    )

    # Long-running jobs: stagger the first run by a random offset and add per-fire
    # jitter so the daily ones never realign on the same instant.
    now = datetime.now(timezone.utc)
    long_jobs = [
        ("check_inactive_users", check_inactive_users, 24),
        ("monitor_role_count", monitor_role_count, ROLE_MONITOR_FREQUENCY_HOURS),
        ("monitor_category_capacity", monitor_category_capacity, 24),
        ("prune_app_logs", prune_app_logs, 24),
    ]
    for job_id, func, hours in long_jobs:
        scheduler.add_job(
            func=func,
            args=[app],
            trigger="interval",
            hours=hours,
            jitter=DAILY_JOB_JITTER,
            next_run_time=now + timedelta(minutes=random.randint(1, DAILY_JOB_START_SPREAD)),
            id=job_id,
            name=job_id,
            replace_existing=True,
        )

    scheduler.start()

    # Shut down the scheduler when Flask stops
    import atexit

    atexit.register(lambda: scheduler.shutdown())
