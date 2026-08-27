# Design

Use a local ignored `.env` derived from the documented example, a randomly generated `WEBUI_SECRET_KEY`, and an ignored SQLite data directory. Do not add configuration code. Start Uvicorn without file watching and Vite directly on their default development ports: the environment blocks file watching and the npm convenience script fetches Pyodide from the network. The first local signup becomes administrator under standard Open WebUI behavior.
