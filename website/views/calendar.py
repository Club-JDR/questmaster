# from flask import render_template, request, jsonify
# from .models import Game, Event, User
# from .games import app

# @app.route('/calendar')
# def calendar():
#     user = get_current_user()  # Implement this function to get the current user
#     role_filter = request.args.get('role', 'both')  # 'gm', 'player', or 'both'

#     # Fetch events based on the user's role
#     if role_filter == 'gm':
#         games = Game.query.filter_by(gm_id=user.id).all()
#     elif role_filter == 'player':
#         games = Game.query.filter(Game.players.any(id=user.id)).all()
#     else:
#         games = Game.query.filter(
#             (Game.gm_id == user.id) | (Game.players.any(id=user.id))
#         ).all()

#     events = []
#     for game in games:
#         for event in game.events:
#             events.append({
#                 'title': game.name,
#                 'start': event.start.strftime('%Y-%m-%dT%H:%M:%S'),
#                 'end': event.end.strftime('%Y-%m-%dT%H:%M:%S'),
#                 'description': f"GM: {game.gm.name}",
#                 'color': 'blue' if game.type == 'campaign' else 'green',
#             })

#     return render_template('calendar.html', events=events)
