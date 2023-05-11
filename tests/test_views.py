def test_my_gm_games(client):
    with client.session_transaction() as session:
        session["user_id"] = "664487064577900594"
        session["username"] = "user"
        session["avatar"] = "avatar.png"
        session["is_gm"] = True
        session["is_admin"] = False
    response = client.get("/mes_annonces/")
    assert response.status_code == 200
    assert b"<h1>Mes annonces</h1>" in response.data
    with client.session_transaction() as session:
        session["is_gm"] = False
    response = client.get("/mes_annonces/")
    assert response.status_code == 403


def test_my_games(client):
    with client.session_transaction() as session:
        session["user_id"] = "664487064577900594"
        session["username"] = "user"
        session["avatar"] = "avatar.png"
        session["is_gm"] = True
        session["is_admin"] = False
    response = client.get("/mes_parties/")
    assert response.status_code == 200
    assert b"<h1>Mes parties en cours</h1>" in response.data


def test_post_game(client):
    with client.session_transaction() as session:
        session["user_id"] = "664487064577900594"
        session["username"] = "user"
        session["avatar"] = "avatar.png"
        session["is_gm"] = True
        session["is_admin"] = False
    # POST NEW GAME
    game_name = "La ville en jaune"
    gm_id = "664487064577900594"
    game_type = "campaign"
    game_length = "20+ sessions"
    game_system = "Cthulhu Hack"
    game_description = """
    Fin juillet 1920, Strasbourg. La ville étouffe sous la chaleur estivale. Vous avez obtenu une place à la soirée de gala de l’hôtel de ville, qui comporte une vente de tickets de loterie dont les bénéfices sont destinés à aider les orphelins de la guerre.
Lorsque vous sortez prendre l’air sur le balcon donnant sur la place Broglie, vous y rencontrez Mr. Charles Bongens, le chef du projet de la Grande Percée, l’air bonhomme, accoudé à la balustrade et fumant une cigarette en regardant les étoiles scintiller dans le ciel.
Alors qu’il commence à se faire tard, vous tendez votre carte à M. Bongens, qui la prend sans hésiter. Il se pourrait qu’il ai besoin de votre aide rapidement.

La Ville en Jaune est une campagne pour Cthulhu Hack. Elle se déroule à Strasbourg dans les année 1920.
Elle a pour cadre le projet de la Grande Percée, un immense projet de rénovation urbaine. Mais il semblerait qu’un projet comme celui-ci attire les convoitises.
La campagne a un ton horrifique modéré et est principalement centrée autour d’enquêtes.
Nous commencerons par un OS d'introduction qui se déroulera en 1890.
    """
    game_restriction = "18+"
    game_restriction_tags = '[{"value":"meurtres","color":"hsl(250,63%,66%)","style":"--tag-bg:hsl(250,63%,66%)"},{"value":"folie","color":"hsl(184,47%,67%)","style":"--tag-bg:hsl(184,47%,67%)"}]'
    game_party_size = 3
    game_party_selection = True
    game_img = "https://www.gameontabletop.com/contenu/image/ks_projet_img/414_rp-Aenk0p_Iwj_2rkY-mk-gdW6nr"
    data = {
        "name": game_name,
        "type": game_type,
        "length": game_length,
        "gm_id": gm_id,
        "system": game_system,
        "description": game_description,
        "restriction": game_restriction,
        "restriction_tags": game_restriction_tags,
        "party_size": game_party_size,
        "party_selection": game_party_selection,
        "img": game_img,
        "action": "open",
        "date": "2023-07-01 20:30",
    }
    response = client.post("/annonce/", data=data)
    assert response.status_code == 200
    assert bytes("<h1>{}</h1>".format(game_name), encoding="UTF-8") in response.data

def test_get_game_details(client):
    pass