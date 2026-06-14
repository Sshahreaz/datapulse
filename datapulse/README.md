# DataPulse

An agentic AI data analyst powered by Claude. Connect to a database, ask questions in plain English, and get SQL queries executed and results explained automatically.

## Features

- **ReAct agent loop** — Claude reasons and acts iteratively using tools until it has a complete answer
- **Multi-source connectors** — SQLite, CSV/Excel, PostgreSQL, MySQL
- **Two tools**: `query_database` (executes SQL) and `detect_anomalies` (IQR-based outlier + null analysis)
- **Streamlit UI** — schema explorer, chat history, and example question shortcuts

## Setup

```bash
pip install streamlit pandas anthropic tabulate
streamlit run app.py
```

Set your Anthropic API key before running:

```bash
export ANTHROPIC_API_KEY=sk-...   # macOS/Linux
$env:ANTHROPIC_API_KEY="sk-..."   # Windows PowerShell
```

## Sample dataset (Olist)

`setup_database.py` loads the [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) CSVs into a local SQLite database with a pre-built `order_summary` view:

```bash
# place the Olist CSVs in data/raw/, then:
python setup_database.py
# → writes data/olist.db
```

Connect DataPulse to `data/olist.db` via the SQLite option in the sidebar.

## Project Structure

```
datapulse/
├── app.py                        # Streamlit frontend
├── setup_database.py             # One-time loader for Olist CSV → SQLite
├── agent/
│   └── core.py                   # ReAct agent loop (Claude Opus 4.8)
└── connectors/
    ├── base.py                   # Abstract base class
    ├── sqlite_connector.py
    ├── csv_connector.py          # Loads CSV/Excel into in-memory SQLite
    ├── postgres_connector.py
    └── mysql_connector.py
```

## Connectors

| Source | Required config |
|---|---|
| SQLite | File path to `.db` file |
| CSV / Excel | One or more `.csv`, `.xlsx`, or `.xls` files |
| PostgreSQL | Host, port, database, user, password |
| MySQL | Host, port, database, user, password |

## Optional dependencies

PostgreSQL and MySQL connectors require additional drivers — only needed if you use those sources:

```bash
pip install psycopg2-binary          # PostgreSQL
pip install mysql-connector-python   # MySQL
```
