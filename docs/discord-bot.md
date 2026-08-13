# Discord Sidekick Bot (Slash Commands)

QuestMaster drives Discord **outward** (creating channels/roles, posting embeds through
`DiscordService`). The sidekick bot adds the **inward** direction: members type slash commands
inside their game's Discord channel and QuestMaster performs the same action a button click
would, then replies ephemerally in Discord.

## Available commands

All commands except `/badges`, `/signaler` and the admin moderation commands are scoped to
the **game's Discord channel** (the game is resolved from the channel the command is run in).
Dates use the `JJ/MM/AAAA HH:MM` format; durations use `3h` / `2h30` forms.

| Command | Description | Who |
| --- | --- | --- |
| `/info` | Compact game summary (announcement URL, role or player list, next session, status) | anyone in the channel |
| `/signaler <message>` | Send an alert to the admins. In a game channel it references the game (participants only, same as the "Signaler" button); anywhere else it carries only the caller and the message | anyone (participants only in a game channel) |
| `/notifier <message>` | Notify the game's players in the channel | GM, admins |
| `/ajouter-session <debut> [duree] [fin]` | Add a game session and post the embed. Without `duree`/`fin`, the game's configured session length is used | GM, admins |
| `/editer-session <debut> <nouveau_debut> [duree] [nouvelle_fin]` | Reschedule the session starting at `debut`. Without `duree`/`nouvelle_fin`, the session keeps its current duration | GM, admins |
| `/supprimer-session <debut>` | Delete the session starting at `debut` | GM, admins |
| `/inscrire <membre>` | Register a member to the game (forced, like the web management flow; the member must hold the Discord player role) | GM, admins |
| `/desinscrire <membre>` | Unregister a member from the game | GM, admins |
| `/ouvrir` | Reopen a closed game to registrations | GM, admins |
| `/fermer` | Close an open game to registrations | GM, admins |
| `/publier` | Publish the channel's announcement if it isn't published yet (e.g. after a silent publish; pure drafts have no channel and are published from the website) | GM, admins |
| `/badges [membre]` | Show a member's trophies (the caller's by default); works in any channel | anyone |
| `/avertir <membre> <raison> [gravite] [article] [lien]` | Record a moderation infraction against a member (same as the admin "Modération" page); nothing is posted publicly and the member is not notified; works in any channel | admins |
| `/infractions <membre>` | List a member's infractions, newest first (mirrors the historical Mee6 `!infractions`); works in any channel | admins |

Bot replies are **ephemeral** (only the invoking user sees them); the side effects (alert
embed, session embed, player notification) are posted publicly through the existing embed
paths, exactly as the web buttons do. A user-facing help page is available in the app under
**Aide → Commandes Discord** (`/aide/commandes-discord/`).

## How it works

The bot uses Discord's **HTTP Interactions** model — no long-lived gateway process:

1. Discord signs each interaction with the application's Ed25519 key and POSTs it to
   `/discord/interactions` (`website/views/discord_interactions.py`).
2. The blueprint verifies the signature over the raw request body against
   `DISCORD_PUBLIC_KEY`. Invalid or missing signatures get a `401`. **The signature is the
   authentication** — no OAuth, JWT, or session is involved; the verified payload already
   contains the caller's Discord user ID.
3. Read-only commands (`/info`) are answered inline in the HTTP response. Mutating commands
   return a **deferred acknowledgement** within Discord's 3-second window, run in a background
   thread (with a Flask app context), and deliver the outcome as a follow-up message.
4. `DiscordCommandService` (`website/services/discord_command.py`) resolves the invoking user
   (`UserService.get_or_create` + `refresh_roles()`) and the game
   (`GameRepository.get_by_channel`), enforces the same GM/admin/participant rules as the web
   views, and calls the **existing services** — no business logic is duplicated.

## Setup

### 1. Configuration

Two environment variables complement the existing Discord settings:

```ini
DISCORD_PUBLIC_KEY=""  # Developer Portal → your app → General Information → Public Key
DISCORD_APP_ID=""      # Application ID; defaults to DISCORD_CLIENT_ID when unset
```

### 2. Register the slash commands

Command definitions live in `website/cli.py` (`SLASH_COMMANDS`). Register (or update) them
with the Flask CLI after each deploy that changes them:

```bash
uv run flask sync-discord-commands
```

This performs a **bulk overwrite** of the guild's application commands
(`PUT /applications/{app_id}/guilds/{guild_id}/commands`). Registration is guild-scoped on
purpose: it propagates instantly (global commands can take up to an hour) and QuestMaster
serves a single guild.

### 3. Set the Interactions Endpoint URL

In the [Discord Developer Portal](https://discord.com/developers/applications), open your
application → **General Information** → **Interactions Endpoint URL** and set it to:

```text
https://<your-host>/discord/interactions
```

Discord immediately sends a signed `PING` to validate the endpoint; QuestMaster answers with
`PONG`, so the URL is accepted as long as `DISCORD_PUBLIC_KEY` is configured and the app is
reachable over HTTPS.

!!! note "Local development"
    The endpoint must be publicly reachable for live testing — use a tunnel such as
    `cloudflared`. For everyday development the pipeline is covered by unit tests that POST
    payloads signed with a locally generated Ed25519 key
    (`tests/views/test_discord_interactions.py`).

## Security notes

- Every request is rejected (`401`) unless the Ed25519 signature over
  `timestamp + raw_body` verifies against `DISCORD_PUBLIC_KEY`.
- The bot trusts only the signed `member.user.id`; it never accepts a user ID as a command
  argument.
- The endpoint is CSRF-exempt (like the JWT API) but signature-protected.
- Mutating commands enforce the same authorization rules as the web views; unauthorized
  callers get an ephemeral refusal and no action is taken.
