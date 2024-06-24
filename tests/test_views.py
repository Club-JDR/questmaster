from bs4 import BeautifulSoup
from conftest import TestConfig
from datetime import datetime

config = TestConfig()


def test_my_gm_games(client):
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.get("/mes_annonces/")
    assert response.status_code == 200
    assert b"<h1>Mes annonces</h1>" in response.data
    with client.session_transaction() as session:
        session["is_gm"] = False
    response = client.get("/mes_annonces/")
    assert response.status_code == 403


def test_my_games(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.get("/mes_parties/")
    assert response.status_code == 200
    assert b"<h1>Mes parties en cours</h1>" in response.data


def test_game_form(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.get("/annonce/")
    assert response.status_code == 403
    with client.session_transaction() as session:
        session["is_gm"] = True
    response = client.get("/annonce/")
    assert response.status_code == 200
    assert b"<h1>Nouvelle annonce</h1>" in response.data


def test_create_system(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    data = {"name": config.sys_name, "icon": config.sys_icon}
    response = client.post("/systems/", data=data, follow_redirects=True)
    assert response.status_code == 403  # Not Admin
    with client.session_transaction() as session:
        session["is_admin"] = True
    response = client.post("/systems/", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert bytes("{}".format(config.sys_name), encoding="UTF-8") in response.data
    assert bytes("{}".format(config.sys_icon), encoding="UTF-8") in response.data
    for form in BeautifulSoup(response.data.decode("utf-8"), "html.parser").find_all(
        "form"
    ):
        for i in form.find_all("input"):
            if i.get("name") == config.sys_name:
                config.game_system = i.get("value")
    response = client.post("/systems/", data=data, follow_redirects=True)
    assert response.status_code == 500  # System name must be unique


def test_edit_system(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    new_name = "{} modifié".format(config.sys_name)
    data = {"name": new_name, "icon": config.sys_icon}
    response = client.post(
        "/systems/{}/".format(config.game_system), data=data, follow_redirects=True
    )
    assert response.status_code == 403  # Not Admin
    with client.session_transaction() as session:
        session["is_admin"] = True
    response = client.post(
        "/systems/{}/".format(config.game_vtt), data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert bytes(new_name, encoding="UTF-8") in response.data
    assert bytes("{}".format(config.sys_icon), encoding="UTF-8") in response.data


def test_create_vtt(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    data = {"name": config.vtt_name, "icon": config.vtt_icon}
    response = client.post("/vtts/", data=data, follow_redirects=True)
    assert response.status_code == 403  # Not Admin
    with client.session_transaction() as session:
        session["is_admin"] = True
    response = client.post("/vtts/", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert bytes("{}".format(config.vtt_name), encoding="UTF-8") in response.data
    assert bytes("{}".format(config.vtt_icon), encoding="UTF-8") in response.data
    for form in BeautifulSoup(response.data.decode("utf-8"), "html.parser").find_all(
        "form"
    ):
        for i in form.find_all("input"):
            if i.get("name") == config.vtt_name:
                config.game_vtt = i.get("value")
    response = client.post("/vtts/", data=data, follow_redirects=True)
    assert response.status_code == 500  # VTT name must be unique


def test_edit_vtt(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    new_name = "{} modifié".format(config.vtt_name)
    data = {"name": new_name, "icon": config.vtt_icon}
    response = client.post(
        "/vtts/{}/".format(config.game_vtt), data=data, follow_redirects=True
    )
    assert response.status_code == 403  # Not Admin
    with client.session_transaction() as session:
        session["is_admin"] = True
    response = client.post(
        "/vtts/{}/".format(config.game_vtt), data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert bytes(new_name, encoding="UTF-8") in response.data
    assert bytes("{}".format(config.vtt_icon), encoding="UTF-8") in response.data


def test_admin_form(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.get("/admin/vtts/")
    assert response.status_code == 403  # Not Admin
    response = client.get("/admin/systems/")
    assert response.status_code == 403  # Not Admin
    with client.session_transaction() as session:
        TestConfig.set_admin_session(session)
    response = client.get("/admin/systems/")
    assert response.status_code == 200
    assert bytes("{}".format(config.sys_icon), encoding="UTF-8") in response.data
    response = client.get("/admin/vtts/")
    assert response.status_code == 200
    assert bytes("{}".format(config.vtt_icon), encoding="UTF-8") in response.data


def test_create_open_game(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    data = {
        "name": config.game_name,
        "type": config.game_type,
        "length": config.game_length,
        "gm_id": config.gm_id,
        "system": config.game_system,
        "vtt": config.game_vtt,
        "description": config.game_description,
        "restriction": config.game_restriction,
        "restriction_tags": config.game_restriction_tags,
        "party_size": config.game_party_size,
        "party_selection": config.game_party_selection,
        "xp": config.game_xp,
        "frequency": config.game_frequency,
        "characters": config.game_characters,
        "complement": config.game_complement,
        "serious": "on",
        "class-action": "min",
        "class-investigation": "maj",
        "class-interaction": "maj",
        "class-horror": "maj",
        "img": config.game_img,
        "action": "open",
        "date": "2023-07-01 20:30",
        "session_length": "3.5",
    }
    response = client.post("/annonce/", data=data, follow_redirects=True)
    assert response.status_code == 403  # fails because not GM
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post("/annonce/", data=data, follow_redirects=True)
    config.game_id = response.request.path.split("/")[-2]
    assert response.status_code == 200
    assert (
        bytes("<h1>{}</h1>".format(config.game_name), encoding="UTF-8") in response.data
    )
    assert '<i class="bi bi-pencil-square"></i> Éditer' in response.data.decode()


def test_add_game_session(client):
    data = {"date_start": "2024-06-07 20:00", "date_end": "2024-06-07 23:00"}
    url = "/annonces/{}/sessions/ajouter".format(config.game_id)
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.post(
        url,
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 403
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        url,
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert 'startDate="2024-06-07"' in response.data.decode()
    assert 'endDate="2024-06-07"' in response.data.decode()


def test_edit_game_session(client):
    data = {"date_start": "2024-06-12 20:00", "date_end": "2024-06-12 23:00"}
    url = "/annonces/{}/sessions/{}/editer".format(config.game_id, config.session_id)
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.post(
        url,
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 403
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        url,
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert 'startDate="2024-06-12"' in response.data.decode()
    assert 'endDate="2024-06-12"' in response.data.decode()


def test_delete_game_session(client):
    url = "/annonces/{}/sessions/{}/supprimer".format(config.game_id, config.session_id)
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.post(
        url,
        follow_redirects=True,
    )
    assert response.status_code == 403
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        url,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert (
        'action="/annonces/{}/sessions/{}/editer"'.format(
            config.game_id, config.session_id
        )
        not in response.data.decode()
    )


def test_search_games(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.get("/annonces/")
    assert response.status_code == 200
    assert b"<h1>Annonces</h1>" in response.data
    assert "Recherche avancée" in response.data.decode()
    response = client.get(
        "/annonces/?name=test&open=on&oneshot=on&all=on&vtt={}&system={}".format(
            config.game_vtt, config.game_system
        )
    )
    assert response.status_code == 200


def test_create_draft_game(client):
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    data = {
        "name": config.game_name2,
        "type": config.game_type2,
        "length": config.game_length2,
        "gm_id": config.gm_id,
        "system": config.game_system,
        "vtt": config.game_vtt,
        "description": config.game_description2,
        "restriction": config.game_restriction2,
        "restriction_tags": "",
        "party_size": config.game_party_size2,
        "img": config.game_img2,
        "action": "draft",
        "date": "2023-11-01 20:30",
        "xp": config.game_xp,
        "frequency": "",
        "characters": config.game_characters2,
        "serious": "on",
        "session_length": "3.5",
    }
    response = client.post("/annonce/", data=data, follow_redirects=True)
    config.game_id2 = response.request.path.split("/")[-2]
    assert response.status_code == 200
    assert (
        bytes("<h1>{}</h1>".format(config.game_name2), encoding="UTF-8")
        in response.data
    )
    assert '<i class="bi bi-pencil-square"></i> Éditer' in response.data.decode()


def test_get_game_details(client):
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    # GET GAME DETAILS AS GAME GM
    response = client.get("/annonces/{}/".format(config.game_id))
    assert response.status_code == 200
    assert (
        bytes("<h1>{}</h1>".format(config.game_name), encoding="UTF-8") in response.data
    )
    assert '<i class="bi bi-pencil-square"></i> Éditer' in response.data.decode()
    assert "S'inscrire" not in response.data.decode()
    # GET GAME DETAILS AS ANOTHER (NON ADMIN) USER should NOT show the actions bar but allow to register
    with client.session_transaction() as session:
        session["user_id"] = config.user_id
        session["is_admin"] = False
    response = client.get("/annonces/{}/".format(config.game_id))
    assert response.status_code == 200
    assert '<i class="bi bi-pencil-square"></i> Éditer' not in response.data.decode()
    assert "S'inscrire" in response.data.decode()
    # GET GAME DETAILS AS ANOTHER ADMIN USER should show the actions bar and allow to register
    with client.session_transaction() as session:
        session["is_admin"] = True
    response = client.get("/annonces/{}/".format(config.game_id))
    assert response.status_code == 200
    assert '<i class="bi bi-pencil-square"></i> Éditer' in response.data.decode()
    assert "S'inscrire" in response.data.decode()


def test_get_open_game_edit_form(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.get("/annonces/{}/editer/".format(config.game_id))
    assert response.status_code == 403
    with client.session_transaction() as session:
        session["is_admin"] = True
    response = client.get("/annonces/{}/editer/".format(config.game_id))
    assert response.status_code == 200
    assert (
        bytes("<h1>Éditer l'annonce</h1>".format(config.game_name), encoding="UTF-8")
        in response.data
    )
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.get("/annonces/{}/editer/".format(config.game_id))
    assert response.status_code == 200
    assert (
        bytes("<h1>Éditer l'annonce</h1>".format(config.game_name), encoding="UTF-8")
        in response.data
    )


def test_get_draft_game_edit_form(client):
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.get("/annonces/{}/editer/".format(config.game_id2))
    assert response.status_code == 200
    assert (
        bytes("<h1>Éditer l'annonce</h1>".format(config.game_name), encoding="UTF-8")
        in response.data
    )
    assert "Publier" in response.data.decode()


def test_edit_publish_game(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    new_description = "Scénario bidon modifié pour les bienfaits des tests."
    data = {
        "name": config.game_name2,
        "type": config.game_type2,
        "length": config.game_length2,
        "gm_id": config.gm_id,
        "system": config.game_system,
        "vtt": config.game_vtt,
        "description": new_description,
        "restriction": config.game_restriction2,
        "restriction_tags": "",
        "party_size": config.game_party_size2,
        "img": config.game_img2,
        "action": "open",
        "date": "2023-11-01 20:30",
        "xp": config.game_xp,
        "frequency": "",
        "characters": config.game_characters2,
        "serious": "on",
        "class-action": "min",
        "class-investigation": "maj",
        "class-interaction": "maj",
        "class-horror": "none",
        "session_length": "3.5",
    }
    response = client.post(
        "/annonces/{}/editer/".format(config.game_id2), data=data, follow_redirects=True
    )
    assert response.status_code == 403
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        "/annonces/{}/editer/".format(config.game_id2), data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert new_description in response.data.decode()
    assert "Brouillon" not in response.data.decode()


def test_close_game(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.post(
        "/annonces/{}/statut/".format(config.game_id),
        data={"status": "closed"},
        follow_redirects=True,
    )
    assert response.status_code == 403
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        "/annonces/{}/statut/".format(config.game_id),
        data={"status": "closed"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Complet" in response.data.decode()


def test_open_game(client):
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        "/annonces/{}/statut/".format(config.game_id),
        data={"status": "open"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Complet" not in response.data.decode()


def test_archive_game(client):
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        "/annonces/{}/statut/".format(config.game_id),
        data={"status": "archived"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert bytes("Archivée".format(config.game_name), encoding="UTF-8") in response.data


def test_register_game(client):
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        "/annonces/{}/inscription/".format(config.game_id2),
        follow_redirects=True,
    )
    assert response.status_code == 403  # cannot register to own game
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.post(
        "/annonces/{}/inscription/".format(config.game_id),
        follow_redirects=True,
    )
    assert response.status_code == 500  # cannot register to archived game
    response = client.post(
        "/annonces/{}/inscription/".format(config.game_id2),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert config.user_id in response.data.decode()
    assert "Complet" in response.data.decode()


def test_manage_game_registration(client):
    with client.session_transaction() as session:
        TestConfig.set_user_session(session)
    response = client.post(
        "/annonces/{}/gerer/".format(config.game_id2),
        follow_redirects=True,
    )
    assert response.status_code == 403  # cannot manage registration if not gamne's GM
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        "/annonces/{}/gerer/".format(config.game_id2),
        data={},  # empty data to unregister everyone
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Aucun·e joueur·euses pour le moment." in response.data.decode()


def test_cleanup(client):
    with client.session_transaction() as session:
        TestConfig.set_gm_session(session)
    response = client.post(
        "/annonces/{}/statut/".format(config.game_id2),
        data={"status": "archived"},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_stats(client):
    response = client.get("/stats/")
    assert response.status_code == 200
    assert (
        datetime.today()
        .replace(day=1, month=datetime.today().month - 1)
        .strftime("%a %d/%m")
        in response.data.decode()
    )
