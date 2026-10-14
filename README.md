# E-commerce FAQ & Order Tracking Bot (Phases 1–4)

A local Rasa Open Source assistant for greetings, farewells, return-policy questions, bot identity, and order tracking. Order status comes from a small SQLite fixture. A minimal Streamlit chat UI sends messages to Rasa's REST channel.

## Prerequisites and compatibility

- Python **3.10** recommended (Rasa Open Source 3.6.21 supports Python 3.8–3.10, not 3.11+).
- Rasa Open Source **3.6.21** and Rasa SDK **3.6.2** are pinned in `requirements.txt`.
- Streamlit **1.41.1** is pinned for the demo UI.
- SQLite is included with Python. No database server, API credentials, or authentication settings are needed for local use.

Create a virtual environment from the project directory. In PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS/Linux, use `python3.10 -m venv .venv` and `source .venv/bin/activate`.

## Initialize the database

The initializer creates 15 fictional orders in `data/orders.sqlite3` and is safe to rerun:

```powershell
python scripts/init_db.py
```

The action server reads `ORDER_DB_PATH`; the default is `data/orders.sqlite3`, relative to the project directory. To use another file, set the same path in the terminals that run the initializer and action server:

```powershell
$env:ORDER_DB_PATH = "data/local-orders.sqlite3"
python scripts/init_db.py
```

The `.gitignore` excludes local SQLite files; initialize a fresh local fixture after checkout.

## Validate, test, and train

```powershell
python -m unittest discover -s tests -v
rasa data validate
rasa train
```

Run the Rasa Open Source dialogue conversation tests after training:

```powershell
rasa test core --stories tests/test_conversations.yml --out results
```

These test stories cover greetings, return policy, tracking with and without an ID, invalid-ID retry, and fallback. Rasa Open Source story tests verify predicted dialogue actions; custom actions are not executed by that test command. The unit tests separately exercise the action and real SQLite repository using temporary databases.

## Start all three local processes

Use three terminals, all opened in the project directory with `.venv` activated. If you chose a custom database path, set `ORDER_DB_PATH` in the initializer/action terminal. No credentials are needed for Rasa's REST input channel; `credentials.yml` enables the `rest:` channel.

**Terminal 1 — custom action server:**

```powershell
rasa run actions
```

**Terminal 2 — Rasa server with REST enabled:**

```powershell
rasa run --enable-api --credentials credentials.yml --endpoints endpoints.yml --port 5005
```

**Terminal 3 — Streamlit chat UI:**

```powershell
streamlit run streamlit_app.py
```

The browser UI sends messages to `http://localhost:5005/webhooks/rest/webhook`. Set `RASA_REST_URL` if Rasa listens at a different base URL or webhook endpoint. The UI retains a per-browser message history and displays friendly messages when Rasa is unreachable or returns a server error.

For an interactive terminal chat instead of Streamlit, stop the Rasa server and run `rasa shell --endpoints endpoints.yml` while Terminal 1 remains active.

## Project structure

```text
.
├── actions.py                  # Form validation and tracking action
├── order_repository.py         # Parameterized SQLite lookup
├── streamlit_app.py            # Minimal chat UI
├── rasa_rest_client.py         # REST transport and error handling
├── credentials.yml             # REST channel (no secrets)
├── endpoints.yml               # Custom action endpoint
├── config.yml / domain.yml     # NLU pipeline, policies, intents, slots, responses
├── data/                       # NLU, stories, rules, and local database
├── scripts/init_db.py          # Recreates the fictional SQLite fixture
└── tests/                      # Unit tests and Rasa conversation test stories
```

The sample data is fictional and intended only for local development. This project has no production order-service integration, authentication, or remote deployment.
