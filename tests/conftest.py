from dotenv import load_dotenv
import pytest

# Load env BEFORE importing app
config = load_dotenv()
import website
import time


class TestConfig:
    gm_id = "664487064577900594"
    user_id = "267928135419297792"
    game_system = 1
    game_vtt = 1
    sys_name = "Cthulhu Hack"
    sys_icon = "https://club-jdr.fr/wp-content/uploads/2021/12/hack.png"
    vtt_name = "Foundry"
    vtt_icon = "https://foundryvtt.wiki/fvtt-solid-512.png"
    game_id = 1
    session_id = 1
    game_id2 = 1
    game_name = "La ville en jaune"
    game_name2 = "Une enquête OKLM"
    game_type = "campaign"
    game_type2 = "oneshot"
    game_length = "20+ sessions"
    game_length2 = "1 session"
    game_description = """
    Fin juillet 1920, Strasbourg. La ville étouffe sous la chaleur estivale. Vous avez obtenu une place à la soirée de gala de l’hôtel de ville, qui comporte une vente de tickets de loterie dont les bénéfices sont destinés à aider les orphelins de la guerre.
Lorsque vous sortez prendre l’air sur le balcon donnant sur la place Broglie, vous y rencontrez Mr. Charles Bongens, le chef du projet de la Grande Percée, l’air bonhomme, accoudé à la balustrade et fumant une cigarette en regardant les étoiles scintiller dans le ciel.
Alors qu’il commence à se faire tard, vous tendez votre carte à M. Bongens, qui la prend sans hésiter. Il se pourrait qu’il ai besoin de votre aide rapidement.

La Ville en Jaune est une campagne pour Cthulhu Hack. Elle se déroule à Strasbourg dans les année 1920.
Elle a pour cadre le projet de la Grande Percée, un immense projet de rénovation urbaine. Mais il semblerait qu’un projet comme celui-ci attire les convoitises.
La campagne a un ton horrifique modéré et est principalement centrée autour d’enquêtes.
Nous commencerons par un OS d'introduction qui se déroulera en 1890.
    """
    game_description2 = """
Retrouverez vous le voleur de la rue de la paix ?
Une aventure solo pour un·e joueur·euse et un·e MJ.

Ce scénario n'existe pas, c'est uniquement une annonce qui sert à faire des tests pour QuestMaster.
    """
    game_restriction = "18+"
    game_restriction2 = "all"
    game_restriction_tags = '[{"value":"meurtres"},{"value":"folie"}]'
    game_party_size = 3
    game_party_size2 = 1
    game_party_selection = "on"
    game_img = "https://www.gameontabletop.com/contenu/image/ks_projet_img/414_rp-Aenk0p_Iwj_2rkY-mk-gdW6nr"
    game_img2 = "https://i.imgur.com/CJQdtXT.jpeg"
    game_xp = "all"
    game_frequency = "bi-weekly"
    game_complement = "Sélection sur questionnaire."
    game_characters = "self"
    game_characters2 = "pregen"

    def set_gm_session(session):
        session["user_id"] = TestConfig.gm_id
        session["username"] = "user"
        session["avatar"] = "avatar.png"
        session["is_gm"] = True
        session["is_admin"] = False

    def set_user_session(session):
        session["user_id"] = TestConfig.user_id
        session["username"] = "user"
        session["avatar"] = "avatar.png"
        session["is_gm"] = False
        session["is_admin"] = False

    def set_admin_session(session):
        session["user_id"] = TestConfig.gm_id
        session["username"] = "user"
        session["avatar"] = "avatar.png"
        session["is_gm"] = True
        session["is_admin"] = True


@pytest.fixture()
def app():
    website.app.config["WTF_CSRF_METHODS"] = []  # disable CSRF for tests
    yield website.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def slow_down_tests():
    yield
    time.sleep(1)
