"""Tests for the custom admin blueprint (DaisyUI panel).

Covers access control plus CRUD round-trips through the new admin routes,
delegating to the existing service layer. Admin edits are database-only
(no Discord side effects), so these tests do not require Discord credentials.
"""

from uuid import uuid4

import pytest

from tests.constants import TEST_ADMIN_USER_ID
from tests.factories import (
    DiscordMessageFactory,
    GameEventFactory,
    GameFactory,
    SpecialEventFactory,
    SystemFactory,
    TrophyFactory,
    UserFactory,
    UserTrophyFactory,
    VttFactory,
)
from website.models import (
    AppSetting,
    Channel,
    DiscordMessage,
    Game,
    PermissionGrant,
    SpecialEvent,
    System,
    Trophy,
    UserTrophy,
    Vtt,
)

# All admin list/index routes that should be gated and render for admins.
ADMIN_LIST_ROUTES = [
    "/admin/",
    "/admin/users/",
    "/admin/games/",
    "/admin/special-events/",
    "/admin/trophies/",
    "/admin/systems/",
    "/admin/vtts/",
    "/admin/channels/",
    "/admin/game-events/",
    "/admin/discord/",
    "/admin/settings/",
]


@pytest.fixture
def admin_client(test_app):
    """A test client whose session is an authenticated admin."""
    client = test_app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = "admin"
        sess["is_admin"] = True
    return client


# -- Access control ----------------------------------------------------------


def test_admin_requires_admin_user(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "test_user"
        sess["is_admin"] = False

    response = client.get("/admin/", follow_redirects=True)
    assert response.status_code == 403


def test_admin_dashboard_loads(admin_client):
    response = admin_client.get("/admin/")
    assert response.status_code == 200
    assert b"QuestMaster Admin" in response.data


@pytest.mark.parametrize("path", ADMIN_LIST_ROUTES)
def test_admin_view_requires_admin_user(client, path):
    with client.session_transaction() as sess:
        sess["user_id"] = "some_user"
        sess["is_admin"] = False

    response = client.get(path)
    assert response.status_code == 403


@pytest.mark.parametrize("path", ADMIN_LIST_ROUTES)
def test_admin_view_accessible_to_admin(admin_client, db_session, path):
    response = admin_client.get(path)
    assert response.status_code == 200


# -- Systems -----------------------------------------------------------------


def test_create_system(admin_client, db_session, mock_csrf):
    response = admin_client.post(
        "/admin/systems/new", data={"name": "Brand New System", "icon": "bns.png"}
    )
    assert response.status_code == 302
    created = db_session.query(System).filter_by(name="Brand New System").first()
    assert created is not None
    assert created.icon == "bns.png"


def test_edit_system(admin_client, db_session, mock_csrf):
    system = SystemFactory(db_session)
    admin_client.post(
        f"/admin/systems/{system.id}/edit", data={"name": "Renamed System", "icon": ""}
    )
    db_session.refresh(system)
    assert system.name == "Renamed System"
    assert system.icon is None


def test_delete_system(admin_client, db_session, mock_csrf):
    system = SystemFactory(db_session)
    admin_client.post(f"/admin/systems/{system.id}/delete")
    assert db_session.get(System, system.id) is None


# -- VTTs --------------------------------------------------------------------


def test_create_vtt(admin_client, db_session, mock_csrf):
    response = admin_client.post("/admin/vtts/new", data={"name": "Owlbear", "icon": ""})
    assert response.status_code == 302
    assert db_session.query(Vtt).filter_by(name="Owlbear").first() is not None


def test_delete_vtt(admin_client, db_session, mock_csrf):
    vtt = VttFactory(db_session)
    admin_client.post(f"/admin/vtts/{vtt.id}/delete")
    assert db_session.get(Vtt, vtt.id) is None


# -- Channels ----------------------------------------------------------------


def test_create_channel(admin_client, db_session, mock_csrf, monkeypatch):
    from unittest.mock import MagicMock

    import website.views.admin.channels as ch

    new_id = "999888777666555444"
    # The local test DB is not wiped between runs; ensure a clean slate.
    existing = db_session.get(Channel, new_id)
    if existing:
        db_session.delete(existing)
        db_session.commit()

    mock_discord = MagicMock()
    mock_discord.create_category.return_value = {"id": new_id}
    monkeypatch.setattr(ch, "discord_service", mock_discord)

    response = admin_client.post("/admin/channels/new", data={"type": "campaign"})
    assert response.status_code == 302
    mock_discord.create_category.assert_called_once()
    channel = db_session.get(Channel, new_id)
    assert channel is not None
    assert channel.type == "campaign"
    assert channel.size == 0

    # Clean up so the row does not leak into other tests / runs.
    db_session.delete(channel)
    db_session.commit()


def test_create_channel_discord_failure_flashes(admin_client, db_session, mock_csrf, monkeypatch):
    from unittest.mock import MagicMock

    import website.views.admin.channels as ch
    from website.exceptions import DiscordAPIError

    mock_discord = MagicMock()
    mock_discord.create_category.side_effect = DiscordAPIError("boom", status_code=500)
    monkeypatch.setattr(ch, "discord_service", mock_discord)

    before = db_session.query(Channel).count()
    response = admin_client.post(
        "/admin/channels/new", data={"type": "campaign"}, follow_redirects=False
    )
    # Re-renders the form (200), no new row persisted.
    assert response.status_code == 200
    assert db_session.query(Channel).count() == before


def test_reconcile_channels(admin_client, db_session, mock_csrf, monkeypatch):
    from unittest.mock import MagicMock

    import website.views.admin.channels as ch

    mock_discord = MagicMock()
    mock_discord.list_guild_channels.return_value = []
    monkeypatch.setattr(ch, "discord_service", mock_discord)

    response = admin_client.post("/admin/channels/reconcile")
    assert response.status_code == 302
    mock_discord.list_guild_channels.assert_called_once()


def test_update_channel_settings(admin_client, db_session, mock_csrf):
    from website.services.setting import (
        CATEGORY_AUTO_THRESHOLD_KEY,
        CATEGORY_NAME_TEMPLATES_KEY,
        SettingsService,
    )

    response = admin_client.post(
        "/admin/channels/settings",
        data={
            "auto_threshold": "40",
            "template_campaign": "CAMP {n}",
            "template_oneshot": "OS {n}",
        },
    )
    assert response.status_code == 302
    service = SettingsService()
    assert service.get_category_auto_threshold() == 40
    assert service.get_category_name_templates()["campaign"] == "CAMP {n}"

    # Clean up so these DB-managed settings do not leak into other tests / runs.
    db_session.query(AppSetting).filter(
        AppSetting.key.in_([CATEGORY_AUTO_THRESHOLD_KEY, CATEGORY_NAME_TEMPLATES_KEY])
    ).delete(synchronize_session=False)
    db_session.commit()


def test_edit_channel(admin_client, db_session, mock_csrf):
    channel = db_session.query(Channel).first()
    original_id = channel.id
    admin_client.post(f"/admin/channels/{channel.id}/edit", data={"type": "oneshot", "size": "42"})
    db_session.refresh(channel)
    assert channel.id == original_id
    assert channel.size == 42


# -- Trophies (badges) -------------------------------------------------------


def test_create_trophy(admin_client, db_session, mock_csrf):
    response = admin_client.post(
        "/admin/trophies/new", data={"name": "Hero of the Realm", "unique": "on", "icon": ""}
    )
    assert response.status_code == 302
    trophy = db_session.query(Trophy).filter_by(name="Hero of the Realm").first()
    assert trophy is not None
    assert trophy.unique is True


def test_delete_trophy(admin_client, db_session, mock_csrf):
    trophy = TrophyFactory(db_session)
    admin_client.post(f"/admin/trophies/{trophy.id}/delete")
    assert db_session.get(Trophy, trophy.id) is None


# -- Special events ----------------------------------------------------------


def test_create_special_event_parses_hex_color(admin_client, db_session, mock_csrf):
    response = admin_client.post(
        "/admin/special-events/new",
        data={"name": "Halloween Bash", "emoji": "🎃", "color": "#ff8800", "active": "on"},
    )
    assert response.status_code == 302
    event = db_session.query(SpecialEvent).filter_by(name="Halloween Bash").first()
    assert event is not None
    assert event.color == 0xFF8800
    assert event.active is True


def test_delete_special_event(admin_client, db_session, mock_csrf):
    event = SpecialEventFactory(db_session)
    admin_client.post(f"/admin/special-events/{event.id}/delete")
    assert db_session.get(SpecialEvent, event.id) is None


def test_special_event_games_lists_linked_games(admin_client, db_session, default_system):
    event = SpecialEventFactory(db_session)
    linked = GameFactory(
        db_session,
        name="Linked Game",
        system_id=default_system.id,
        special_event_id=event.id,
    )
    unlinked = GameFactory(db_session, name="Unlinked Game", system_id=default_system.id)

    resp = admin_client.get(f"/admin/special-events/{event.id}/games")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert linked.name in body
    assert unlinked.name not in body


def test_special_event_games_unknown_event_redirects(admin_client):
    resp = admin_client.get("/admin/special-events/999999/games")
    assert resp.status_code == 302


# -- User/trophy associations ------------------------------------------------


def test_award_user_trophy(admin_client, db_session, mock_csrf):
    trophy = TrophyFactory(db_session)
    user = UserFactory(db_session)
    response = admin_client.post(
        f"/admin/users/{user.id}/trophies/award",
        data={"trophy_id": str(trophy.id), "quantity": "3"},
    )
    assert response.status_code == 302
    ut = db_session.get(UserTrophy, (user.id, trophy.id))
    assert ut is not None
    assert ut.quantity == 3


def test_award_unique_trophy_rejects_duplicate(admin_client, db_session, mock_csrf):
    trophy = TrophyFactory(db_session, unique=True)
    user = UserFactory(db_session)
    UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=1)

    response = admin_client.post(
        f"/admin/users/{user.id}/trophies/award",
        data={"trophy_id": str(trophy.id), "quantity": "1"},
    )
    # Validation error -> flashed and redirected, still a single row.
    assert response.status_code == 302
    rows = db_session.query(UserTrophy).filter_by(user_id=user.id, trophy_id=trophy.id).all()
    assert len(rows) == 1


def test_edit_user_trophy_quantity(admin_client, db_session, mock_csrf):
    trophy = TrophyFactory(db_session)
    user = UserFactory(db_session)
    ut = UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=1)
    admin_client.post(f"/admin/users/{user.id}/trophies/{trophy.id}/edit", data={"quantity": "5"})
    db_session.refresh(ut)
    assert ut.quantity == 5


def test_delete_user_trophy(admin_client, db_session, mock_csrf):
    trophy = TrophyFactory(db_session)
    user = UserFactory(db_session)
    UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=1)
    admin_client.post(f"/admin/users/{user.id}/trophies/{trophy.id}/delete")
    assert db_session.get(UserTrophy, (user.id, trophy.id)) is None


# -- Trophy increment / decrement quick actions (Phase 2) --------------------


def test_increment_user_trophy(admin_client, db_session, mock_csrf):
    trophy = TrophyFactory(db_session)
    user = UserFactory(db_session)
    ut = UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=1)
    response = admin_client.post(f"/admin/users/{user.id}/trophies/{trophy.id}/increment")
    assert response.status_code == 302
    db_session.refresh(ut)
    assert ut.quantity == 2


def test_decrement_user_trophy_above_one(admin_client, db_session, mock_csrf):
    trophy = TrophyFactory(db_session)
    user = UserFactory(db_session)
    ut = UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=3)
    response = admin_client.post(f"/admin/users/{user.id}/trophies/{trophy.id}/decrement")
    assert response.status_code == 302
    db_session.refresh(ut)
    assert ut.quantity == 2


def test_decrement_user_trophy_at_one_removes_record(admin_client, db_session, mock_csrf):
    trophy = TrophyFactory(db_session)
    user = UserFactory(db_session)
    UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=1)
    response = admin_client.post(f"/admin/users/{user.id}/trophies/{trophy.id}/decrement")
    assert response.status_code == 302
    assert db_session.get(UserTrophy, (user.id, trophy.id)) is None


def test_unique_trophy_hides_increment_buttons(admin_client, db_session):
    trophy = TrophyFactory(db_session, unique=True)
    user = UserFactory(db_session)
    UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=1)
    response = admin_client.get(f"/admin/users/{user.id}/trophies")
    assert response.status_code == 200
    body = response.data.decode()
    # The increment action for this unique pair must be absent from the page.
    assert f"/admin/users/{user.id}/trophies/{trophy.id}/increment" not in body


# -- Settings (config overrides) ---------------------------------------------


@pytest.fixture
def clean_app_settings(db_session):
    """Clear app_setting overrides before and after a settings test."""
    db_session.query(AppSetting).delete()
    db_session.commit()
    yield
    db_session.query(AppSetting).delete()
    db_session.commit()


def test_settings_page_shows_env_fallback(admin_client, db_session):
    response = admin_client.get("/admin/settings/")
    assert response.status_code == 200
    # The overridable keys are surfaced as form fields.
    assert 'name="DISCORD_GM_ROLE_ID"' in response.data.decode()


def test_settings_save_creates_override(admin_client, db_session, mock_csrf, clean_app_settings):
    response = admin_client.post(
        "/admin/settings/",
        data={"DISCORD_GM_ROLE_ID": "custom-gm-role"},
    )
    assert response.status_code == 302
    stored = db_session.get(AppSetting, "DISCORD_GM_ROLE_ID")
    assert stored.value == "custom-gm-role"
    assert stored.updated_by_id == "admin"


def test_settings_save_empty_clears_override(
    admin_client, db_session, mock_csrf, clean_app_settings
):
    db_session.add(AppSetting(key="POSTS_CHANNEL_ID", value="old-channel"))
    db_session.commit()
    admin_client.post("/admin/settings/", data={"POSTS_CHANNEL_ID": ""})
    assert db_session.get(AppSetting, "POSTS_CHANNEL_ID") is None


def test_settings_page_shows_direct_permissions_toggle(admin_client, db_session):
    response = admin_client.get("/admin/settings/")
    assert response.status_code == 200
    assert 'name="direct_permissions"' in response.data.decode()


def test_permissions_save_enables_direct_mode(
    admin_client, db_session, mock_csrf, clean_app_settings
):
    response = admin_client.post(
        "/admin/settings/permissions/",
        data={"direct_permissions": "on", "role_auto_threshold": "200"},
    )
    assert response.status_code == 302
    assert db_session.get(AppSetting, "discord_use_direct_permissions").value == "true"
    assert db_session.get(AppSetting, "discord_role_auto_threshold").value == "200"


def test_permissions_save_unchecked_disables_direct_mode(
    admin_client, db_session, mock_csrf, clean_app_settings
):
    db_session.add(AppSetting(key="discord_use_direct_permissions", value="true"))
    db_session.commit()
    admin_client.post(
        "/admin/settings/permissions/",
        data={"role_auto_threshold": "230"},
    )
    assert db_session.get(AppSetting, "discord_use_direct_permissions").value == "false"


def test_permissions_save_persists_games_per_page(
    admin_client, db_session, mock_csrf, clean_app_settings
):
    response = admin_client.post(
        "/admin/settings/permissions/",
        data={
            "role_auto_threshold": "200",
            "dashboard_agenda_limit": "10",
            "dashboard_open_limit": "8",
            "games_per_page": "24",
        },
    )
    assert response.status_code == 302
    assert db_session.get(AppSetting, "games_per_page").value == "24"


def test_permissions_save_rejects_out_of_bounds_games_per_page(
    admin_client, db_session, mock_csrf, clean_app_settings
):
    db_session.add(AppSetting(key="games_per_page", value="12"))
    db_session.commit()
    admin_client.post(
        "/admin/settings/permissions/",
        data={
            "role_auto_threshold": "200",
            "dashboard_agenda_limit": "10",
            "dashboard_open_limit": "8",
            "games_per_page": "999",
        },
    )
    # Out-of-bounds value is rejected; the stored value is left unchanged.
    assert db_session.get(AppSetting, "games_per_page").value == "12"


# -- Users -------------------------------------------------------------------


def test_edit_user(admin_client, db_session, mock_csrf):
    user = UserFactory(db_session)
    admin_client.post(
        f"/admin/users/{user.id}/edit",
        data={"name": "Renamed User", "not_player_as_of": "2026-01-01T00:00"},
    )
    db_session.refresh(user)
    assert user.name == "Renamed User"
    assert user.not_player_as_of is not None


def test_user_games_lists_gm_and_player_games(admin_client, db_session, default_system):
    user = UserFactory(db_session)
    gm_game = GameFactory(db_session, name="GMed Game", gm_id=user.id, system_id=default_system.id)
    played_game = GameFactory(db_session, name="Played Game", system_id=default_system.id)
    played_game.players.append(user)
    db_session.flush()

    resp = admin_client.get(f"/admin/users/{user.id}/games")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "GMed Game" in body
    assert "Played Game" in body


def test_user_games_unknown_user_redirects(admin_client):
    resp = admin_client.get("/admin/users/000000000000000000/games")
    assert resp.status_code == 302


# -- Games -------------------------------------------------------------------


def test_admin_full_field_game_edit(admin_client, db_session, mock_csrf, default_system):
    game = GameFactory(db_session, status="open", system_id=default_system.id)
    data = {
        "name": "Edited By Admin",
        "slug": game.slug,
        "type": "campaign",
        "status": "closed",
        "gm_id": TEST_ADMIN_USER_ID,
        "system_id": str(default_system.id),
        "vtt_id": "",
        "length": "5 sessions",
        "session_length": "4.0",
        "date": "2026-03-01T20:00",
        "frequency": "weekly",
        "party_size": "6",
        "party_selection": "on",
        "xp": "beginners",
        "characters": "pregen",
        "restriction": "16+",
        "restriction_tags": "horreur, violence",
        "description": "A brand new description.",
        "complement": "",
        "class-action": "1",
        "class-investigation": "2",
        "class-interaction": "0",
        "class-horror": "2",
        "serious": "on",
        "epic": "on",
        "img": "",
        "channel": "",
        "msg_id": "",
        "role": "",
        "special_event_id": "",
    }
    response = admin_client.post(f"/admin/games/{game.id}/edit", data=data)
    assert response.status_code == 302
    db_session.refresh(game)
    assert game.name == "Edited By Admin"
    assert game.type == "campaign"
    assert game.status == "closed"
    assert game.party_size == 6
    assert game.party_selection is True
    assert game.restriction == "16+"
    assert game.restriction_tags == "horreur, violence"
    assert game.classification == {
        "action": 1,
        "investigation": 2,
        "interaction": 0,
        "horror": 2,
    }
    assert sorted(game.ambience) == ["epic", "serious"]
    assert float(game.session_length) == 4.0


def test_admin_delete_game(admin_client, db_session, mock_csrf, default_system):
    game = GameFactory(db_session, system_id=default_system.id)
    game_id = game.id
    admin_client.post(f"/admin/games/{game_id}/delete")
    assert db_session.get(Game, game_id) is None


def test_game_events_list_renders(admin_client, db_session, default_system):
    game = GameFactory(db_session, system_id=default_system.id)
    GameEventFactory(db_session, game_id=game.id, action="create", description="Created via test")
    response = admin_client.get("/admin/game-events/")
    assert response.status_code == 200
    assert b"Created via test" in response.data


# -- Search & pagination -----------------------------------------------------


def test_list_search_filters_results(admin_client, db_session, mock_csrf):
    """A simple list view filters rows by the ``q`` query parameter."""
    token = uuid4().hex[:10]
    match = SystemFactory(db_session, name=f"Matching {token}")
    other = SystemFactory(db_session, name=f"Unrelated {uuid4().hex[:10]}")

    response = admin_client.get(f"/admin/systems/?q={token}")
    body = response.data.decode()

    assert response.status_code == 200
    assert match.name in body
    assert other.name not in body


# -- Discord messaging (Phase 3) ---------------------------------------------


@pytest.fixture
def post_channel(db_session):
    """Register a postable channel in the managed settings list; return its ID.

    Removes any leftover entry first (the settings list persists in the DB
    across local runs) and cleans up afterwards so the fixture is idempotent.
    """
    from website.services.setting import SettingsService

    service = SettingsService()
    channel_id = "555000111222333444"
    service.remove_post_channel(channel_id)
    service.add_post_channel("Annonces", channel_id)
    yield channel_id
    service.remove_post_channel(channel_id)


@pytest.fixture
def mock_discord_msg_api(monkeypatch):
    """Patch the Discord API behind the admin message service."""
    from unittest.mock import MagicMock

    import website.views.admin.discord_messages as dm

    mock = MagicMock()
    mock.create_message.return_value = {"id": "msg-new-1"}
    mock.update_message.return_value = {}
    mock.delete_message.return_value = {}
    monkeypatch.setattr(dm.discord_message_service, "discord", mock)
    return mock


def test_compose_plain_message(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    mock_discord_msg_api.create_message.return_value = {"id": "msg-plain-1"}
    response = admin_client.post(
        "/admin/discord/compose",
        data={"channel": post_channel, "content": "Hello world"},
    )
    assert response.status_code == 302
    mock_discord_msg_api.create_message.assert_called_once_with(
        post_channel, content="Hello world", embeds=None, components=[]
    )
    message = db_session.query(DiscordMessage).filter_by(discord_msg_id="msg-plain-1").first()
    assert message is not None
    assert message.content == "Hello world"
    assert message.embeds is None
    assert message.channel_id == post_channel
    assert message.channel_label == "Annonces"


def test_compose_embed_message(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    mock_discord_msg_api.create_message.return_value = {"id": "msg-embed-1"}
    response = admin_client.post(
        "/admin/discord/compose",
        data={
            "channel": post_channel,
            "embed_title": "Embed title",
            "embed_description": "Embed body",
            "embed_color": "#00ff00",
        },
    )
    assert response.status_code == 302
    sent_embeds = mock_discord_msg_api.create_message.call_args.kwargs["embeds"]
    assert sent_embeds[0]["title"] == "Embed title"
    assert sent_embeds[0]["color"] == 0x00FF00
    message = db_session.query(DiscordMessage).filter_by(discord_msg_id="msg-embed-1").first()
    assert message is not None
    assert message.is_embed
    assert message.embeds[0]["title"] == "Embed title"
    assert message.embeds[0]["color"] == 0x00FF00


def test_compose_content_and_multi_embed_with_buttons(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    mock_discord_msg_api.create_message.return_value = {"id": "msg-multi-1"}
    response = admin_client.post(
        "/admin/discord/compose",
        data={
            "channel": post_channel,
            "content": "Heads up",
            "embed_title": ["First", "Second"],
            "embed_description": ["", "Body"],
            "embed_color": ["#00ff00", "#0000ff"],
            "button_label": ["Site", ""],
            "button_url": ["https://example.com", ""],
        },
    )
    assert response.status_code == 302
    call = mock_discord_msg_api.create_message.call_args
    assert call.kwargs["content"] == "Heads up"
    assert len(call.kwargs["embeds"]) == 2
    assert call.kwargs["components"][0]["components"][0]["url"] == "https://example.com"
    message = db_session.query(DiscordMessage).filter_by(discord_msg_id="msg-multi-1").first()
    assert message.content == "Heads up"
    assert len(message.embeds) == 2
    assert message.buttons == [{"label": "Site", "url": "https://example.com"}]


def test_compose_empty_message_rejected(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    before = db_session.query(DiscordMessage).count()
    response = admin_client.post(
        "/admin/discord/compose",
        data={"channel": post_channel, "content": ""},
    )
    assert response.status_code == 200
    mock_discord_msg_api.create_message.assert_not_called()
    assert db_session.query(DiscordMessage).count() == before


def test_compose_invalid_button_url_rejected(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    before = db_session.query(DiscordMessage).count()
    response = admin_client.post(
        "/admin/discord/compose",
        data={
            "channel": post_channel,
            "content": "Hi",
            "button_label": "Bad",
            "button_url": "not-a-url",
        },
    )
    assert response.status_code == 200
    mock_discord_msg_api.create_message.assert_not_called()
    assert db_session.query(DiscordMessage).count() == before


def test_compose_unknown_channel_rejected(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    before = db_session.query(DiscordMessage).count()
    response = admin_client.post(
        "/admin/discord/compose",
        data={"channel": "NOT_A_CHANNEL", "content": "x"},
    )
    # Validation error -> form re-rendered, nothing sent or persisted.
    assert response.status_code == 200
    mock_discord_msg_api.create_message.assert_not_called()
    assert db_session.query(DiscordMessage).count() == before


def test_compose_discord_error_not_persisted(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    from website.exceptions import DiscordAPIError

    mock_discord_msg_api.create_message.side_effect = DiscordAPIError("boom", status_code=500)
    before = db_session.query(DiscordMessage).count()
    response = admin_client.post(
        "/admin/discord/compose",
        data={"channel": post_channel, "content": "Hello"},
    )
    assert response.status_code == 200
    assert db_session.query(DiscordMessage).count() == before


def test_edit_embed_message(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    message = DiscordMessageFactory(
        db_session, channel_id=post_channel, embeds=[{"title": "Old title"}]
    )
    response = admin_client.post(
        f"/admin/discord/{message.id}/edit",
        data={"channel": post_channel, "embed_title": "New title", "embed_description": "Updated"},
    )
    assert response.status_code == 302
    mock_discord_msg_api.update_message.assert_called_once()
    db_session.refresh(message)
    assert message.embeds[0]["title"] == "New title"
    assert message.embeds[0]["description"] == "Updated"


def test_edit_change_channel_resends_and_deletes(
    admin_client, db_session, mock_csrf, mock_discord_msg_api, post_channel
):
    from website.services.setting import SettingsService

    settings = SettingsService()
    settings.add_post_channel("Autre", "999000111222333444")
    message = DiscordMessageFactory(
        db_session,
        channel_id=post_channel,
        discord_msg_id="old-msg",
        embeds=[{"title": "Hi"}],
    )
    mock_discord_msg_api.create_message.return_value = {"id": "moved-msg"}

    response = admin_client.post(
        f"/admin/discord/{message.id}/edit",
        data={"channel": "999000111222333444", "embed_title": "Hi"},
    )
    assert response.status_code == 302
    mock_discord_msg_api.create_message.assert_called_once()
    mock_discord_msg_api.delete_message.assert_called_once_with("old-msg", post_channel)
    db_session.refresh(message)
    assert message.channel_id == "999000111222333444"
    assert message.discord_msg_id == "moved-msg"
    settings.remove_post_channel("999000111222333444")


def test_delete_discord_message(admin_client, db_session, mock_csrf, mock_discord_msg_api):
    message = DiscordMessageFactory(db_session)
    message_id = message.id
    response = admin_client.post(f"/admin/discord/{message_id}/delete")
    assert response.status_code == 302
    mock_discord_msg_api.delete_message.assert_called_once()
    assert db_session.get(DiscordMessage, message_id) is None


def test_add_post_channel(admin_client, db_session, mock_csrf):
    from website.services.setting import SettingsService

    service = SettingsService()
    service.remove_post_channel("777111222333444555")
    response = admin_client.post(
        "/admin/discord/channels/new",
        data={"label": "Taverne", "channel_id": "777111222333444555"},
    )
    assert response.status_code == 302
    channels = service.get_post_channels()
    assert {"label": "Taverne", "channel_id": "777111222333444555"} in channels
    service.remove_post_channel("777111222333444555")


def test_remove_post_channel(admin_client, db_session, mock_csrf):
    from website.services.setting import SettingsService

    service = SettingsService()
    service.remove_post_channel("777111222333444555")
    service.add_post_channel("Taverne", "777111222333444555")
    response = admin_client.post("/admin/discord/channels/777111222333444555/delete")
    assert response.status_code == 302
    assert not service.is_post_channel("777111222333444555")


def test_list_search_no_match_shows_empty(admin_client, db_session):
    """Searching for a term with no matches renders the empty-state row."""
    response = admin_client.get(f"/admin/systems/?q=nomatch-{uuid4().hex}")
    assert response.status_code == 200
    assert "Aucun système." in response.data.decode()


def test_list_paginates_and_preserves_search(admin_client, db_session, mock_csrf):
    """Results beyond one page are split, with search preserved across pages."""
    token = uuid4().hex[:10]
    # 26 systems (> ADMIN_PAGE_SIZE of 25) so a second page is required.
    for i in range(26):
        SystemFactory(db_session, name=f"PageSys-{i:02d}-{token}")

    page_one = admin_client.get(f"/admin/systems/?q={token}").data.decode()
    # First page holds the first 25 (00–24), not the 26th (index 25).
    assert "PageSys-00-" in page_one
    assert "PageSys-25-" not in page_one
    # Pagination nav points to page 2 while keeping the search term.
    assert "page=2" in page_one
    assert f"q={token}" in page_one

    page_two = admin_client.get(f"/admin/systems/?q={token}&page=2").data.decode()
    assert "PageSys-25-" in page_two
    assert "PageSys-00-" not in page_two


def test_game_events_search_spans_relationships(admin_client, db_session, default_system):
    """Audit-trail search matches the related game's slug."""
    token = uuid4().hex[:10]
    game = GameFactory(db_session, slug=f"slug-{token}", system_id=default_system.id)
    GameEventFactory(db_session, game_id=game.id, action="create", description="Audit row")

    hit = admin_client.get(f"/admin/game-events/?q={token}")
    assert hit.status_code == 200
    assert b"Audit row" in hit.data

    miss = admin_client.get(f"/admin/game-events/?q=absent-{uuid4().hex}")
    assert miss.status_code == 200
    assert b"Audit row" not in miss.data


def test_user_trophies_page_lists_user_badges(admin_client, db_session, mock_csrf):
    """The per-user badges page lists the trophies that user owns."""
    user = UserFactory(db_session)
    trophy = TrophyFactory(db_session)
    UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=1)

    response = admin_client.get(f"/admin/users/{user.id}/trophies")
    assert response.status_code == 200
    assert trophy.name in response.data.decode()


# -- Granular permissions (RBAC) ---------------------------------------------


@pytest.fixture
def clean_grants(db_session):
    """Empty the permission_grant table and cache around a permissions test."""
    from website.extensions import cache

    cache.clear()
    db_session.query(PermissionGrant).delete()
    db_session.commit()
    yield
    db_session.query(PermissionGrant).delete()
    db_session.commit()
    cache.clear()


def _delegated_client(test_app, permissions):
    """Return a client whose session is a non-admin holding ``permissions``."""
    client = test_app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = "delegate"
        sess["is_admin"] = False
        sess["permissions"] = list(permissions)
    return client


def test_delegated_user_reaches_granted_section(test_app, db_session):
    """A non-admin with vtt.manage can open the VTTs section."""
    client = _delegated_client(test_app, ["vtt.manage"])
    assert client.get("/admin/vtts/").status_code == 200


def test_delegated_user_blocked_from_other_section(test_app, db_session):
    """A non-admin with only vtt.manage is blocked from systems."""
    client = _delegated_client(test_app, ["vtt.manage"])
    assert client.get("/admin/systems/").status_code == 403


def test_delegated_user_blocked_from_admin_only_section(test_app, db_session):
    """A delegated user cannot reach admin-only sections (settings)."""
    client = _delegated_client(test_app, ["vtt.manage"])
    assert client.get("/admin/settings/").status_code == 403


def test_user_without_grants_bounced_from_admin(test_app, db_session):
    """A logged-in user with no grants cannot reach the admin panel at all."""
    client = _delegated_client(test_app, [])
    assert client.get("/admin/").status_code == 403


def test_delegated_sidebar_lists_only_granted_sections(test_app, db_session):
    """The admin sidebar for a delegated user shows only their sections."""
    client = _delegated_client(test_app, ["vtt.manage"])
    body = client.get("/admin/").data.decode()
    assert "/admin/vtts/" in body
    assert "/admin/systems/" not in body
    assert "/admin/settings/" not in body


def test_admin_sees_permissions_section(admin_client, db_session):
    """An admin reaches the new permissions management section."""
    assert admin_client.get("/admin/permissions/").status_code == 200


def test_grant_permission_persists(admin_client, db_session, mock_csrf, clean_grants):
    """Granting a capability to a role persists a grant row."""
    response = admin_client.post(
        "/admin/permissions/grant",
        data={
            "permission_key": "vtt.manage",
            "subject_type": "role",
            "subject_id": "role-123",
        },
    )
    assert response.status_code == 302
    grant = (
        db_session.query(PermissionGrant)
        .filter_by(permission_key="vtt.manage", subject_id="role-123")
        .one_or_none()
    )
    assert grant is not None
    assert grant.subject_type == "role"


def test_grant_permission_invalid_flashes_error(admin_client, db_session, mock_csrf, clean_grants):
    """An unknown capability key is rejected and nothing is persisted."""
    response = admin_client.post(
        "/admin/permissions/grant",
        data={"permission_key": "bogus.key", "subject_type": "role", "subject_id": "r-1"},
    )
    assert response.status_code == 302
    assert db_session.query(PermissionGrant).count() == 0


def test_revoke_permission_removes_grant(admin_client, db_session, mock_csrf, clean_grants):
    """Revoking removes the grant row."""
    grant = PermissionGrant(permission_key="vtt.manage", subject_type="user", subject_id="u-9")
    db_session.add(grant)
    db_session.commit()
    response = admin_client.post(f"/admin/permissions/{grant.id}/revoke")
    assert response.status_code == 302
    assert db_session.get(PermissionGrant, grant.id) is None
