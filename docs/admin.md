# Admin Panel

QuestMaster ships a custom administration panel mounted at **`/admin/`**, built with the
same DaisyUI + Tailwind layout as the rest of the app (it replaced the legacy Flask-Admin
panel). Each section is a thin Flask view in `website/views/admin/` that delegates to the
existing [service layer](architecture/services.md) — no business logic lives in the admin
views.

## Access

The panel is restricted to **administrators**. A `before_request` guard on the admin
blueprint rejects any request whose session is not an authenticated admin
(`session["is_admin"]`), raising an `UnauthorizedError` (HTTP 403). The admin role is
derived from Discord at login (the `DISCORD_ADMIN_ROLE_ID` role).

Admins reach the panel from the **Admin** dropdown in the main navbar, which lists every
sub-section. The same list is shown in the sidebar inside the panel.

## Sections

| Section | Route | What it does |
| --- | --- | --- |
| Dashboard | `/admin/` | Landing page with links to every section |
| Utilisateurs | `/admin/users/` | List users; edit display name and activity status; view a user's games and badges |
| Annonces | `/admin/games/` | List games; full-field edit; delete |
| Événements | `/admin/special-events/` | CRUD for special (themed) events |
| Badges | `/admin/trophies/` | CRUD for trophy **definitions** |
| Systèmes | `/admin/systems/` | CRUD for RPG systems |
| VTTs | `/admin/vtts/` | CRUD for virtual tabletops |
| Catégories (salons) | `/admin/channels/` | CRUD for Discord channel categories |
| Journaux | `/admin/game-events/` | Read-only game audit trail (most recent events) |
| Messages Discord | `/admin/discord/` | Manage postable channels; compose, send, edit and delete Discord messages (see below) |
| Paramètres | `/admin/settings/` | Runtime configuration overrides (see below) |

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

## Discord Messages

The **Messages Discord** section lets admins send, edit and delete Discord messages —
plain text or rich embeds — to a configured channel, without leaving the app. It also
manages the list of channels that can be posted into.

The list page (`/admin/discord/`) has two actions in its header — **Ajouter un salon** and
**Composer un message** — and shows the **postable channels** first, then the **sent
messages**.

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
  The list is searchable and paginated.
- **Compose** (`/admin/discord/compose`) — pick a target channel, choose **Texte** (plain
  `content`) or **Embed** (title, description, color, footer, image URL), and send.
- **Edit** (`/admin/discord/<id>/edit`) — change the message and push the update to
  Discord. The **channel and message type are fixed** once sent (Discord messages cannot
  move channels or change kind).
- **Delete** (`POST /admin/discord/<id>/delete`) — removes the message from Discord and
  deletes the stored record.

Behaviour and guarantees (implemented in `DiscordMessageService`, which wraps
[`DiscordService`](architecture/services.md#website.services.DiscordService)):

- **Discord first, then database.** A `DiscordMessage` row is only persisted *after*
  Discord confirms the send/edit. If the Discord API call fails, the error is flashed, the
  form is re-rendered with the entered values preserved, and **nothing is stored**.
- **Deletion is best-effort on Discord.** The record is removed even if the message was
  already deleted on Discord, keeping the admin list consistent.
- **Channels are validated.** The target must be one of the configured postable channels;
  a free-typed or unknown channel ID is rejected.

## Settings

The **Paramètres** section (`/admin/settings/`) manages runtime configuration overrides.

!!! warning
    Changing these settings can break the application — the form is fenced in a red box.
    The currently effective value is shown under each field; leave a field empty to fall
    back to the environment value.

A subset of operational Discord identifiers (guild, role and channel IDs) can be overridden
at runtime and stored in the `app_setting` table, taking precedence over the
environment-backed `app.config`. Secrets (bot token, client secret, JWT key, database URI)
are **never** overridable and always come from the environment. Resolution and the
overridable allowlist live in
[`SettingsService`](architecture/services.md#website.services.SettingsService).
