"""Application-wide constants and enumerations."""

# Game Types
GAME_TYPE_ONESHOT = "oneshot"
GAME_TYPE_CAMPAIGN = "campaign"
GAME_TYPES = (GAME_TYPE_ONESHOT, GAME_TYPE_CAMPAIGN)

# Game Status
GAME_STATUS_DRAFT = "draft"
GAME_STATUS_OPEN = "open"
GAME_STATUS_CLOSED = "closed"
GAME_STATUS_ARCHIVED = "archived"
GAME_STATUS = (
    GAME_STATUS_DRAFT,
    GAME_STATUS_OPEN,
    GAME_STATUS_CLOSED,
    GAME_STATUS_ARCHIVED,
)
GAME_STATUS_LABELS = {
    GAME_STATUS_OPEN: "ouverte",
    GAME_STATUS_CLOSED: "fermée",
    GAME_STATUS_ARCHIVED: "archivée",
}

# Game Frequencies
GAME_FREQ_WEEKLY = "weekly"
GAME_FREQ_BI_WEEKLY = "bi-weekly"
GAME_FREQ_MONTHLY = "monthly"
GAME_FREQ_OTHER = "other"
GAME_FREQUENCIES = (
    GAME_FREQ_WEEKLY,
    GAME_FREQ_BI_WEEKLY,
    GAME_FREQ_MONTHLY,
    GAME_FREQ_OTHER,
)

# Experience Levels
GAME_XP_ALL = "all"
GAME_XP_BEGINNERS = "beginners"
GAME_XP_SEASONED = "seasoned"
GAME_XP = (GAME_XP_ALL, GAME_XP_BEGINNERS, GAME_XP_SEASONED)

# Character Creation
GAME_CHAR_WITH_GM = "with_gm"
GAME_CHAR_SELF = "self"
GAME_CHAR_PREGEN = "pregen"
GAME_CHAR_CHOICE = "choice"
GAME_CHAR = (
    GAME_CHAR_WITH_GM,
    GAME_CHAR_SELF,
    GAME_CHAR_PREGEN,
    GAME_CHAR_CHOICE,
)

# Restrictions
RESTRICTION_ALL = "all"
RESTRICTION_16_PLUS = "16+"
RESTRICTION_18_PLUS = "18+"
RESTRICTIONS = (RESTRICTION_ALL, RESTRICTION_16_PLUS, RESTRICTION_18_PLUS)

# Ambiences
AMBIENCE_CHILL = "chill"
AMBIENCE_SERIOUS = "serious"
AMBIENCE_COMIC = "comic"
AMBIENCE_EPIC = "epic"
AMBIENCES = (
    AMBIENCE_CHILL,
    AMBIENCE_SERIOUS,
    AMBIENCE_COMIC,
    AMBIENCE_EPIC,
)

# Event Actions
EVENT_ACTION_CREATE = "create"
EVENT_ACTION_EDIT = "edit"
EVENT_ACTION_DELETE = "delete"
EVENT_ACTION_CREATE_SESSION = "create-session"
EVENT_ACTION_EDIT_SESSION = "edit-session"
EVENT_ACTION_DELETE_SESSION = "delete-session"
EVENT_ACTION_REGISTER = "register"
EVENT_ACTION_UNREGISTER = "unregister"
EVENT_ACTION_ALERT = "alert"
EVENT_ACTIONS = (
    EVENT_ACTION_CREATE,
    EVENT_ACTION_EDIT,
    EVENT_ACTION_DELETE,
    EVENT_ACTION_CREATE_SESSION,
    EVENT_ACTION_EDIT_SESSION,
    EVENT_ACTION_DELETE_SESSION,
    EVENT_ACTION_REGISTER,
    EVENT_ACTION_UNREGISTER,
    EVENT_ACTION_ALERT,
)

# Discord
DISCORD_API_BASE_URL = "https://discord.com/api/v10"
PLAYER_ROLE_PERMISSION = "563362270661696"
GM_ROLE_PERMISSION = "2815265163693120"

# Discord role limits
# A Discord guild is hard-capped at 250 roles. When the count nears this limit,
# the scheduler auto-enables direct per-player channel permissions for new games
# so that no further roles are consumed. The threshold at which this kicks in is
# admin-configurable (DB-backed); this constant is only its default value.
DISCORD_ROLE_LIMIT = 250
DISCORD_ROLE_AUTO_THRESHOLD_DEFAULT = 230
# How long (seconds) to cache the guild role count shown on the admin settings page.
DISCORD_ROLE_COUNT_CACHE_TIMEOUT = 3600

# Discord channel categories
DISCORD_CATEGORY_CHANNEL_LIMIT = 50  # Discord hard cap: channels per category.
# Fill level at which a fresh category is auto-provisioned (90% of the limit by
# default). Admin-configurable (DB-backed); this constant is only the fallback.
DISCORD_CATEGORY_AUTO_THRESHOLD_DEFAULT = 45
DISCORD_CHANNEL_TYPE_TEXT = 0  # Discord channel type: GUILD_TEXT.
DISCORD_CHANNEL_TYPE_CATEGORY = 4  # Discord channel type: GUILD_CATEGORY.

# Category name templates, keyed by game type. ``{n}`` is the per-type sequence number.
CATEGORY_NAME_TEMPLATES = {
    GAME_TYPE_CAMPAIGN: "🎲 CAMPAGNES {n} 📖",
    GAME_TYPE_ONESHOT: "🎲 ONE SHOTS {n} 📖",
}

# Discord message components (buttons)
DISCORD_COMPONENT_ACTION_ROW = 1  # Component type: action row (button container).
DISCORD_COMPONENT_BUTTON = 2  # Component type: button.
DISCORD_BUTTON_STYLE_LINK = 5  # Button style: link (opens a URL, no interaction).
DISCORD_MAX_BUTTONS_PER_ROW = 5  # Discord cap: buttons per action row.
DISCORD_BUTTON_LABEL_MAX = 80  # Discord cap: characters in a button label.
DISCORD_EMBED_LIMIT = 10  # Discord cap: embeds per message.

# Site
SITE_BASE_URL = "https://questmaster.club-jdr.fr"

# Discord Embed Colors
EMBED_COLOR_BLUE = 0x2196F3
EMBED_COLOR_GREEN = 0x4CB944
EMBED_COLOR_YELLOW = 0xFFCF48
EMBED_COLOR_RED = 0xF34242
EMBED_COLOR_DEFAULT = 0x5865F2

# Badge IDs
BADGE_OS_ID = 1
BADGE_OS_GM_ID = 2
BADGE_CAMPAIGN_ID = 3
BADGE_CAMPAIGN_GM_ID = 4

# Discord
DEFAULT_AVATAR = "/static/img/avatar.webp"
AVATAR_BASE_URL = "https://cdn.discordapp.com/avatars/{}/{}"

# Pagination
GAMES_PER_PAGE = 12  # Default card-grid page size; admin-overridable at runtime.
GAMES_PER_PAGE_MAX = 60  # Upper bound for the admin-configurable card-grid page size.
API_DEFAULT_PAGE = 1
API_DEFAULT_PER_PAGE = 20
API_MAX_PER_PAGE = 100
ADMIN_PAGE_SIZE = 25

# Dashboard (admin-configurable limits use the *_DEFAULT values as fallbacks).
DASHBOARD_AGENDA_LIMIT_DEFAULT = 10  # Upcoming sessions listed in the agenda.
DASHBOARD_OPEN_LIMIT_DEFAULT = 8  # Latest open announcements shown on the dashboard.
DASHBOARD_LIMIT_MAX = 30  # Upper bound for the admin-configurable dashboard limits.
DASHBOARD_AGENDA_PAST = 3  # Recent past sessions shown before the upcoming ones (context).
DASHBOARD_RYTHME_MONTHS = 12  # Months of activity shown in the "Rythme" chart.
DASHBOARD_TOP_SYSTEMS = 3  # Number of systems listed in each "Top systèmes" ranking.
DASHBOARD_STATS_CACHE_TIMEOUT = 300  # Seconds to cache a user's computed dashboard stats.

# Routes
GAME_DETAILS_ROUTE = "annonces.get_game_details"
SEARCH_GAMES_ROUTE = "annonces.search_games"

# Time Formats
DEFAULT_TIMEFORMAT = "%Y-%m-%d %H:%M"
HUMAN_TIMEFORMAT = "%a %d/%m - %Hh%M"

# Error Messages
MSG_ADMIN_ACCESS_REQUIRED = "Admin access required."

# Cache Timeouts (seconds)
CACHE_USER_PROFILE_TIMEOUT = 60 * 60 * 24  # 24 hours
CACHE_USER_PROFILE_404_TIMEOUT = 60 * 60 * 24 * 7  # 7 days

# Error Templates
TEMPLATE_403 = "403.html"
TEMPLATE_404 = "404.html"
TEMPLATE_500 = "500.html"
