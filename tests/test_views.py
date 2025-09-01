from unittest.mock import patch
import pytest


@pytest.fixture
def logged_in_admin(test_app, admin_user):
    client = test_app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
    return client


@pytest.fixture
def logged_in_user(test_app, regular_user):
    client = test_app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = regular_user.id
    return client


def test_my_gm_games(logged_in_admin, logged_in_user):
    response = logged_in_admin.get("/mes_annonces/")
    assert response.status_code == 200
    assert b"Mes annonces" in response.data
    response = logged_in_user.get("/mes_annonces/")
    assert response.status_code == 403


def test_my_games(logged_in_user):
    response = logged_in_user.get("/mes_parties/")
    assert response.status_code == 200
    assert b"Mes parties en cours" in response.data


def test_game_form(logged_in_admin, logged_in_user):
    response = logged_in_user.get("/annonce/")
    assert response.status_code == 403
    response = logged_in_admin.get("/annonce/")
    assert response.status_code == 200
    assert b"Nouvelle annonce" in response.data
    assert b"Enregistrer" in response.data
    assert b"Publier" in response.data


def test_search(test_app, default_system, default_vtt):
    filters = f"?name=&system={default_system}6&vtt={default_vtt}&campaign=on&open=on&closed=on&archived=on&draft=on&all=on&16%2B=on&18%2B=on"
    client = test_app.test_client()
    response = client.get(f"/annonces/{filters}")
    assert response.status_code == 200


@patch("flask_wtf.csrf.validate_csrf", return_value=True)
def test_e2e_scenario_1(
    mock_csrf,
    logged_in_admin,
    logged_in_user,
    admin_user,
    default_system,
    default_vtt,
    regular_user,
):
    # Create open Game
    title = "Les Masques de Nyarlathotep"
    data = {
        "name": title,
        "type": "campaign",
        "length": "20+ sessions",
        "gm_id": admin_user.id,
        "system": default_system.id,
        "vtt": default_vtt.id,
        "description": """En avril 1919, Roger Carlyle, un richissime play-boy New-Yorkais, décide de financer et d'organiser une expédition archéologique. Accompagné des plus éminents égyptologues, photographes et médecins du moment, l'expédition fait une escale de quelques semaines à Londres afin de préparer les fouilles et d'étudier divers documents, avant de se rendre en Égypte, dans les régions de Gizeh, de Saqqarah et de Dahchour. Après deux mois de recherches, l'expédition décide d'aller se reposer quelques semaines au Kenya. Le groupe part pour un safari-photo de plusieurs jours le 3 août, et disparait. Il apparaît rapidement qu'il s'agit d'un crime à caractère raciste, et plusieurs membres d'une tribu kényane sont jugés et pendus. L'expédition de secours dirigée par la sœur de Roger Carlyle découvre un an plus tard les restes de l'expédition. Si les corps ne sont plus identifiables, le contenu des bagages prouve qu'il s'agit de l'expédition disparue.

Quelques années plus tard, Jackson Elias, un reporter spécialisé dans les cultes religieux d'Afrique et d'Asie, envoie un télégramme à son éditeur, lui indiquant qu'il possède des informations sur l'expédition Carlyle et qu'il dispose de documents prouvant que certains de ses membres ne sont pas morts. Il charge son vieil ami de trouver une équipe d'investigateurs susceptibles de l'aider dans ses recherches, et leur donne rendez-vous dans un hôtel.
        """,
        "restriction": "18+",
        "restriction_tags": '[{"value":"meurtres"},{"value":"folie"}]',
        "party_size": "1",
        "xp": "all",
        "frequency": "bi-weekly",
        "characters": "self",
        "complement": "",
        "serious": "on",
        "class-action": "2",
        "class-investigation": "2",
        "class-interaction": "2",
        "class-horror": "2",
        "img": "https://anubisarchives.com/content/images/2018/12/cthulhu3.jpg",
        "action": "open",
        "date": "2025-07-01 20:30",
        "session_length": "3.5",
    }
    response = logged_in_user.post("/annonce/", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == "/annonces/"
    assert "Vous devez être MJ pour poster une annonce." in response.data.decode()
    response = logged_in_admin.post("/annonce/", data=data, follow_redirects=True)
    assert response.status_code == 200
    slug = response.request.path.strip("/").split("/")[-1]
    assert slug == "les-masques-de-nyarlathotep-par-notsag"
    assert all(
        text in response.data.decode()
        for text in [
            title,
            "editButton",
            "manageButton",
            "Libre",
            "statusButton",
            "archiveButton",
            "Cloner",
        ]
    )

    # Add session
    data = {"date_start": "2025-07-07 23:00", "date_end": "2025-07-07 20:00"}
    response = logged_in_admin.post(
        f"/annonces/{slug}/sessions/ajouter/", data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert (
        "Impossible d'ajouter une session qui se termine avant de commencer"
        in response.data.decode()
    )
    data = {"date_start": "2025-07-07 20:00", "date_end": "2025-07-07 23:00"}
    response = logged_in_admin.post(
        f"/annonces/{slug}/sessions/ajouter/", data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert 'startDate="2025-07-07"' in response.data.decode()
    assert 'endDate="2025-07-07"' in response.data.decode()

    # Edit session
    data = {"date_start": "2025-07-07 23:00", "date_end": "2025-07-07 20:00"}
    response = logged_in_admin.post(
        f"/annonces/{slug}/sessions/2/editer/", data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert (
        "Impossible d'ajouter une session qui se termine avant de commencer"
        in response.data.decode()
    )
    data = {"date_start": "2025-07-08 20:00", "date_end": "2025-07-08 23:00"}
    response = logged_in_admin.post(
        f"/annonces/{slug}/sessions/2/editer/", data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert 'startDate="2025-07-08"' in response.data.decode()
    assert 'endDate="2025-07-08"' in response.data.decode()

    # Get stats with two sessions
    response = logged_in_user.get("/stats/?year=2025&month=7")
    assert response.status_code == 200
    assert "Statistiques" in response.data.decode()
    assert "Les Masques de Nyarlathotep" in response.data.decode()
    assert (
        '<h6 class="text-primary">Appel de Cthulhu v7 <small class="text-muted">(1 campagne)</small></h6>'
        in response.data.decode()
    )

    # Get calendar info
    response = logged_in_user.get(
        "/api/calendar/?start=2025-06-01T00:00:00+02:00&end=2025-07-13T00:00:00+02:00"
    )
    assert response.status_code == 200
    assert '"start":"2025-07-01T20:30:00"' in response.data.decode()
    assert '"title":"Les Masques de Nyarlathotep par Notsag"' in response.data.decode()

    # Remove session
    data = {"date_start": "2025-07-08 20:00", "date_end": "2025-07-08 23:00"}
    response = logged_in_admin.post(
        f"/annonces/{slug}/sessions/2/supprimer/", data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert 'startDate="2025-07-08"' not in response.data.decode()

    # User do not see any actions but can register
    response = logged_in_user.get(f"/annonces/{slug}/")
    assert response.status_code == 200
    assert all(
        text not in response.data.decode()
        for text in [
            "editButton",
            "manageButton",
            "statusButton",
            "archiveButton",
            "Cloner",
        ]
    )
    assert response.data.decode().count("Libre") == 1
    assert "S'inscrire" in response.data.decode()

    # Close Game
    response = logged_in_admin.post(
        f"/annonces/{slug}/statut/", data={"status": "closed"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Complet" in response.data.decode()
    assert f"Annonce {title} fermée." in response.data.decode()
    assert "Ouvrir" in response.data.decode()

    # User cannot register a closed game
    response = logged_in_user.post(
        f"/annonces/{slug}/inscription/", follow_redirects=True
    )
    assert response.status_code == 200
    assert response.data.decode().count("Libre") == 1
    assert "Ce jeu est fermé aux inscriptions." in response.data.decode()

    # Open Game
    response = logged_in_admin.post(
        f"/annonces/{slug}/statut/", data={"status": "open"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Complet" not in response.data.decode()
    assert f"Annonce {title} ouverte." in response.data.decode()
    assert "Close" in response.data.decode()

    # GM cannot register to its own game
    response = logged_in_admin.post(
        f"/annonces/{slug}/inscription/", follow_redirects=True
    )
    assert response.status_code == 200
    assert (
        "Vous ne pouvez pas vous inscrire à votre propre partie."
        in response.data.decode()
    )

    # User can register, Game is full -> closed
    response = logged_in_user.post(
        f"/annonces/{slug}/inscription/", follow_redirects=True
    )
    assert response.status_code == 200
    assert response.data.decode().count("Libre") == 0
    assert "Vous êtes inscrit·e." in response.data.decode()
    assert "Complet" in response.data.decode()

    # User can signal something on the game
    data = {"alertMessage": "Le MJ ne vient plus."}
    response = logged_in_user.post(
        f"/annonces/{slug}/alert/", follow_redirects=True, data=data
    )
    assert response.status_code == 200
    assert "Signalement effectué." in response.data.decode()

    # Archive Game
    response = logged_in_admin.post(
        f"/annonces/{slug}/statut/",
        data={"status": "archived", "award_trophies": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert all(
        text not in response.data.decode()
        for text in ["editButton", "manageButton", "statusButton", "archiveButton"]
    )
    assert "Cloner" in response.data.decode()
    assert "Archivée" in response.data.decode()
    assert f"Annonce {title} archivée." in response.data.decode()
    assert "Annonce archivée. Badges distribués." in response.data.decode()

    # Get trophies
    response = logged_in_user.get("/badges/", follow_redirects=True)
    assert response.status_code == 200
    assert "Badge Campagne (1)" in response.data.decode()

    # Get trophies someone else's trophies
    response = logged_in_user.get(
        f"/badges/?user_id={admin_user.id}", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Badge Campagne GM (1)" in response.data.decode()

    # Get trophies leaderboard
    response = logged_in_user.get("/badges/classement/", follow_redirects=True)
    assert response.status_code == 200


@patch("flask_wtf.csrf.validate_csrf", return_value=True)
def test_e2e_scenario_2(
    mock_csrf,
    logged_in_admin,
    logged_in_user,
    admin_user,
    regular_user,
    default_system,
    default_vtt,
):
    # Create draft Game
    title = "La Nécropole"
    data = {
        "name": title,
        "type": "oneshot",
        "length": "1 session",
        "gm_id": admin_user.id,
        "system": default_system.id,
        "vtt": default_vtt.id,
        "description": """Quelles horreurs antiques renferme la tombe récemment découverte au cœur de la Vallée des Rois, en Égypte ?
        Debout au sommet des marches qui s’enfoncent dans les ténèbres, le moment est mal choisi pour vous laisser troubler par les superstitions locales et les malheureux incidents survenus à l’ouverture du tombeau de Toutankhamon…""",
        "restriction": "16+",
        "restriction_tags": "[]",
        "party_size": "4",
        "xp": "all",
        "frequency": "",
        "characters": "pregen",
        "complement": "",
        "serious": "on",
        "class-action": "2",
        "class-investigation": "2",
        "class-interaction": "1",
        "class-horror": "2",
        "img": "https://shop.novalisgames.com/product/image/large/escth13fr_illu1_20220112.jpg",
        "action": "draft",
        "date": "2025-07-10 20:30",
        "session_length": "3.5",
    }
    response = logged_in_admin.post("/annonce/", data=data, follow_redirects=True)
    assert response.status_code == 200
    slug = response.request.path.strip("/").split("/")[-1]
    assert slug == "la-necropole-par-notsag"
    assert all(
        text in response.data.decode()
        for text in [
            title,
            "editButton",
            "manageButton",
            "Libre",
            "Brouillon",
            "archiveButton",
        ]
    )

    # Get edit form
    response = logged_in_admin.get(f"/annonces/{slug}/editer/")
    assert response.status_code == 200
    assert "Vous êtes en train de modifier une annonce." in response.data.decode()
    assert "Enregistrer" in response.data.decode()
    assert "Publier" in response.data.decode()

    # Edit draft Game
    data["complement"] = "Scénario mortel pour les PJs."
    response = logged_in_admin.post(
        f"/annonces/{slug}/editer/", data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Annonce modifiée." in response.data.decode()
    assert "Scénario mortel pour les PJs." in response.data.decode()

    # GM add a player
    response = logged_in_admin.post(
        f"/annonces/{slug}/gerer/",
        data={"action": "add", "discord_id": regular_user.id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert response.data.decode().count("Libre") == 3

    # GM clears players
    response = logged_in_admin.post(
        f"/annonces/{slug}/gerer/", data={"action": "manage"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert response.data.decode().count("Libre") == 4

    # Open Game without posting
    data["action"] = "open-silent"
    response = logged_in_admin.post(
        f"/annonces/{slug}/editer/", data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Annonce modifiée et ouverte." in response.data.decode()
    assert "Scénario mortel pour les PJs." in response.data.decode()

    # Post game afterwards
    data["action"] = "publish"
    response = logged_in_admin.post(
        f"/annonces/{slug}/editer/", data=data, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Annonce publiée avec succès." in response.data.decode()

    # Archive Game
    response = logged_in_admin.post(
        f"/annonces/{slug}/statut/", data={"status": "archived"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert all(
        text not in response.data.decode()
        for text in ["editButton", "manageButton", "statusButton", "archiveButton"]
    )
    assert "Cloner" in response.data.decode()
    assert "Archivée" in response.data.decode()
    assert f"Annonce {title} archivée." in response.data.decode()

    # Get clone Game form
    response = logged_in_admin.get(f"/annonces/{slug}/cloner/")
    assert response.status_code == 200
    assert "Vous êtes en train de cloner une annonce." in response.data.decode()
    assert "Enregistrer" in response.data.decode()
    assert "Publier" in response.data.decode()

    # Clone Game in draft
    data["action"] = "draft"
    response = logged_in_admin.post("/annonce/", data=data, follow_redirects=True)
    assert response.status_code == 200
    slug = response.request.path.strip("/").split("/")[-1]
    assert slug == "la-necropole-par-notsag-2"
    assert all(
        text in response.data.decode()
        for text in [title, "editButton", "manageButton", "Libre", "archiveButton"]
    )
    # Delete draft
    logged_in_admin.post(
        f"/annonces/{slug}/statut/", data={"status": "deleted"}, follow_redirects=True
    )


def test_calendar(logged_in_user):
    response = logged_in_user.get("/calendrier/")
    assert response.status_code == 200
    assert "Le Calendrier du Club" in response.data.decode()


def test_demo(client):
    response = client.get("/demo/")
    assert response.status_code == 200
    assert "La Tombe de l'Annihilation" in response.data.decode()
    assert "Le Pensionnaire" in response.data.decode()


def test_demo_inscription(client):
    response = client.get("/demo/inscription/")
    assert response.status_code == 200
    assert "La Tombe de l'Annihilation" in response.data.decode()
    assert "S'inscrire" in response.data.decode()


def test_demo_post(client):
    response = client.get("/demo/poster/")
    assert response.status_code == 200
    assert "Nouvelle annonce" in response.data.decode()


def test_demo_gerer(client):
    response = client.get("/demo/gerer/")
    assert response.status_code == 200
    assert "La Tombe de l'Annihilation" in response.data.decode()
    assert "editButton" in response.data.decode()
