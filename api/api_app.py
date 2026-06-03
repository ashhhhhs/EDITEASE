"""Compatibility entrypoint for the full EditEase API server.

Older local commands may still run `python api/api_app.py`. Keep that path
working by exposing the real Flask app instead of the retired demo API.
"""

import config
from api.api_server import app


if __name__ == "__main__":
    app.run(host=config.API_HOST, port=config.API_PORT, debug=config.API_DEBUG)
