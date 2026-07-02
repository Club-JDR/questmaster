# Admin Panel

QuestMaster ships a custom administration panel mounted at **`/admin/`**, built with the
same DaisyUI + Tailwind layout as the rest of the app (it replaced the legacy Flask-Admin
panel). Each section is a thin Flask view in `website/views/admin/` that delegates to the
existing [service layer](architecture/services.md) — no business logic lives in the admin
views.

## Access

The panel is open to **administrators** and to **delegated users** who hold at least one
granted capability (see [Permissions](#permissions-rbac)). A `before_request` guard on the
admin blueprint rejects any session that is neither an admin (`session["is_admin"]`) nor
holds any permission, raising an `UnauthorizedError` (HTTP 403). The admin role is derived
from Discord at login (the `DISCORD_ADMIN_ROLE_ID` role).

- **Admins** are superusers: they implicitly hold the full capability catalog and see
  every sub-section.
- **Delegated users** see — and can reach — only the sub-sections their granted
  capabilities unlock. Each route is additionally fenced by a `require_permission`
  decorator, so the panel guard alone is not enough to act on a section.

The navbar **Admin** dropdown and the in-panel sidebar are filtered to the sections the
current session may use.

## Sections

| Section | Route | What it does |
| --- | --- | --- |
| Dashboard | `/admin/` | Landing page with links to every section |
| Utilisateurs | `/admin/users/` | List users; edit display name and activity status; view a user's games and badges |
| Annonces | `/admin/games/` | List games; full-field edit; delete |
| Événements | `/admin/special-events/` | CRUD for special (themed) events; view an event's games |
| Badges | `/admin/trophies/` | CRUD for trophy **definitions** |
| Systèmes | `/admin/systems/` | CRUD for RPG systems |
| VTTs | `/admin/vtts/` | CRUD for virtual tabletops |
| Catégories (salons) | `/admin/channels/` | Manage Discord channel categories — create, auto-provision, reconcile sizes (see below) |
| Journaux | `/admin/game-events/` | Read-only game audit trail (most recent events) |
| Messages Discord | `/admin/discord/` | Manage postable channels; compose, send, edit and delete Discord messages (see below) |
| Permissions | `/admin/permissions/` | Grant/revoke granular admin capabilities to Discord roles or users (RBAC, see below) |
| Paramètres | `/admin/settings/` | Runtime configuration overrides and operational settings (see below) |

List views support a search box (`?q=`) and pagination where relevant.

## Trophies

Trophy management is split in two:

- **Badges** (`/admin/trophies/`) manage trophy *definitions* (name, icon, and whether the
  trophy is `unique`).
- A user's awarded trophies are managed from that **user's page** (`/admin/users/<id>/trophies`).
  Each awarded trophy row has one-click **+1 / −1** quick actions:
    - **+1** awards one more of the trophy (`TrophyService.award`).
    - **−1** decrements the quantity, and **removes the record entirely when it would reach
      0** (quantity never drops below 1).
    - For trophies marked `unique=True`, the +1/−1 buttons are hidden and the row shows a
      *Unique* badge instead — a unique trophy cannot be awarded more than once.

## Channel Categories

The **Catégories (salons)** section (`/admin/channels/`) manages the Discord **categories**
that game channels are grouped under. Each [`Channel`](architecture/models.md#website.models.Channel)
row tracks a category's Discord ID, its game `type` (one-shot or campaign), and its current
`size` (number of game channels inside it). Discord caps a category at **50 channels**, so
the app spreads games across several categories per type.

- **Create** (`/admin/channels/new`) — provisions a **real Discord category** (not just a
  registered ID). It is named from the per-type template with the next sequence number
  (e.g. `🎲 CAMPAGNES 2 📖`), created on Discord, then stored locally with `size = 0`.
- **Recompter les salons** (`POST /admin/channels/reconcile`) — re-counts each category's
  text channels on Discord and corrects any drifted `size`. Categories at or above the
  auto-create threshold are flagged **« Presque pleine »** in the list.
- **Edit / Delete** — adjust or remove a tracked category row.

### Category settings & auto-provisioning

The bottom of the page has a **Paramètres des catégories** form
(`POST /admin/channels/settings`) with two DB-managed settings owned by
[`SettingsService`](architecture/services.md#website.services.SettingsService):

- **Seuil d'auto-création** — the per-category fill level (1…50) at which the type is
  considered full.
- **Modèles de nom** — one name template per game type; each must contain the `{n}`
  sequence placeholder.

A daily scheduler job (`monitor_category_capacity`) reconciles sizes and then, for each game
type, **auto-provisions a fresh category** when every existing category of that type is at
or above the threshold (it also bootstraps a first category for a type that has none yet).
The category creation/auto-provision logic lives in
[`ChannelService`](architecture/services.md#website.services.ChannelService).

## Discord Messages

The **Messages Discord** section lets admins send, edit and delete Discord messages to a
configured channel, without leaving the app. A message combines, in any mix, plain
**content**, one or more **embeds** and a row of link **buttons**. It also manages the list
of channels that can be posted into.

The list page (`/admin/discord/`) has two actions in its header — **Ajouter un salon** and
**Composer un message** — and shows the **postable channels** first, then the **sent
messages grouped by channel**.

### Postable channels

The channels you can post into are an **admin-managed list** (no code change needed to add
one), stored as a single JSON value under the `discord_post_channels` setting key and owned
by [`SettingsService`](architecture/services.md#website.services.SettingsService)
(`get_post_channels`, `add_post_channel`, `remove_post_channel`, `is_post_channel`).

- **Add** (`/admin/discord/channels/new`) — a form page (like Systems/VTTs) taking a human
  label and a Discord channel ID.
- **Remove** (`POST /admin/discord/channels/<channel_id>/delete`) — from the channels list.

### Messages

- **List** (`/admin/discord/`) — every message sent through the panel is recorded as a
  [`DiscordMessage`](architecture/models.md#website.models.DiscordMessage) so it can be
  found, edited or deleted later, without anyone needing to remember Discord message IDs.
  The list is searchable and paginated, and messages are **grouped by channel**.
- **Compose** (`/admin/discord/compose`) — a two-pane editor (form + **live preview**):
  pick a target channel, optionally type **content**, add up to **10 embeds** (title,
  description, color, footer, image URL) and up to **5 link buttons** (label + URL). A
  message must have at least content or one embed.
- **Edit** (`/admin/discord/<id>/edit`) — change the message and push the update to
  Discord. The **channel can be changed**: because Discord cannot move a message, doing so
  re-sends it to the new channel and deletes the original.
- **Delete** (`POST /admin/discord/<id>/delete`) — removes the message from Discord and
  deletes the stored record.

There is **no message "type"**: a message is simply the combination of content, embeds and
buttons it carries (`is_embed` is derived from whether it has any embeds). Embeds and
buttons are stored as JSON lists on the `DiscordMessage` row.

### Link buttons

Buttons are **link buttons** (Discord button style 5): a label plus an http(s) URL that
opens when clicked. They need no interaction handling, so they work over the REST API
without a gateway connection. Button helpers live in
[`website/utils/discord_components.py`](architecture/utils.md) (`clean_link_buttons`
validates the rows; `build_link_button_rows` builds the Discord `components` payload).

Game announcement embeds also carry a link button: the former inline "Pour s'inscrire" URL
field is now an **S'inscrire** button to the game page. It is omitted while the game is
**closed** (complet) and restored when the game reopens, kept in sync whenever the
announcement embed is refreshed.

Behaviour and guarantees (implemented in `DiscordMessageService`, which wraps
[`DiscordService`](architecture/services.md#website.services.DiscordService)):

- **Discord first, then database.** A `DiscordMessage` row is only persisted *after*
  Discord confirms the send/edit. If the Discord API call fails, the error is flashed, the
  form is re-rendered with the entered values preserved, and **nothing is stored**.
- **Deletion is best-effort on Discord.** The record is removed even if the message was
  already deleted on Discord, keeping the admin list consistent.
- **Channels are validated.** The target must be one of the configured postable channels;
  a free-typed or unknown channel ID is rejected.

## Permissions (RBAC)

The **Permissions** section (`/admin/permissions/`) delegates slices of the admin panel to
non-admin users without making them full administrators.

- **Capabilities are a fixed catalog defined in code** (`website/permissions.py`) — stable
  keys such as `vtt.manage`, `trophy.manage`, `discord.send` or `permissions.manage` that
  the route decorators reference at compile time. Each capability unlocks one admin
  sub-section.
- **Grants — who holds what — live in the database** ([`PermissionGrant`](architecture/models.md#website.models.PermissionGrant)).
  A grant ties one capability to a **subject**: either a Discord **role** (every member of
  that role inherits it) or an individual **user**.

The page lists every catalog capability with its current grants; admins can **grant** a
capability to a role or user and **revoke** any grant. Granting an existing (capability,
subject) pair is idempotent.

Enforcement lives in
[`PermissionService`](architecture/services.md#website.services.PermissionService):

- **Admins implicitly hold the whole catalog.** For everyone else the effective set is the
  union of grants matching the user's Discord role IDs and their own user ID.
- A user's resolved permission set is **cached for 5 minutes** (mirroring Discord role
  resolution). A *user*-subject grant change invalidates that user immediately; a *role*-
  subject change propagates with the cache TTL.
- The session's permissions filter the navbar/sidebar, and each route is fenced by a
  `require_permission(<key>)` decorator — the panel guard alone never authorises an action.

## Settings

The **Paramètres** section (`/admin/settings/`) manages runtime configuration overrides and
fully DB-managed operational settings.

!!! warning
    Changing these settings can break the application — the form is fenced in a red box.
    The currently effective value is shown under each field; leave a field empty to fall
    back to the environment value.

### Configuration overrides (DB → env)

A subset of operational Discord identifiers (guild, role and channel IDs) can be overridden
at runtime and stored in the `app_setting` table, taking precedence over the
environment-backed `app.config`. Secrets (bot token, client secret, JWT key, database URI)
are **never** overridable and always come from the environment. Resolution and the
overridable allowlist live in
[`SettingsService`](architecture/services.md#website.services.SettingsService).

### Operational settings (fully DB-managed)

These keys live only in the database (no environment fallback) and fall back to a code
default when unset:

| Setting | What it controls |
| --- | --- |
| Direct-permissions mode | When enabled, new games grant players access via per-channel permission overwrites instead of a dedicated Discord role |
| Role auto-threshold | Guild role count at which the scheduler turns direct-permissions mode on automatically |
| Dashboard agenda / open limits | Number of agenda and open-game items shown on the personalised landing dashboard |
| Cards per page | Number of game cards shown per page on the public card grid |

The Discord **category** auto-provisioning settings (auto-create threshold and per-type name
templates) are also DB-managed by `SettingsService`, but their admin form lives on the
[Channel Categories](#channel-categories) page rather than here.
