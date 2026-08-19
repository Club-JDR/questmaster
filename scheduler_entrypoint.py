"""Entry point for the dedicated `scheduler` docker-compose service.

Creates the Flask app — which starts APScheduler when ``QM_RUN_SCHEDULER=1``
(see `website/__init__.py`) — then blocks forever so the container stays up.
Job execution happens on APScheduler's own background thread; no web server
is started here, the app object only provides the app context jobs need.
"""

import signal

from website import create_app

app = create_app()

signal.pause()
