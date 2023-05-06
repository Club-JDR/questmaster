from website.views import games


def test_get_game_details(client):
    pass


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
