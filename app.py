import tempfile
import os

import streamlit as st

from agent.core import agent_turn
from connectors import CONNECTOR_MAP

st.set_page_config(page_title="DataPulse", page_icon="📊", layout="wide")

st.title("📊 DataPulse")
st.caption("Agentic AI for your data — powered by Claude")

# ── Sidebar: connection setup ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Connect to Data")
    db_type = st.selectbox("Data source", list(CONNECTOR_MAP.keys()))

    config = {}

    if db_type == "SQLite":
        path = st.text_input("Database file path", placeholder="/path/to/database.db")
        config = {"path": path}

    elif db_type == "CSV / Excel":
        uploaded = st.file_uploader(
            "Upload files", type=["csv", "xlsx", "xls"], accept_multiple_files=True
        )
        files = []
        if uploaded:
            for f in uploaded:
                suffix = os.path.splitext(f.name)[1]
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tmp.write(f.read())
                tmp.flush()
                table_name = os.path.splitext(f.name)[0].replace(" ", "_").replace("-", "_")
                files.append({"path": tmp.name, "table": table_name})
        config = {"files": files}

    elif db_type in ("PostgreSQL", "MySQL"):
        default_port = 5432 if db_type == "PostgreSQL" else 3306
        config["host"] = st.text_input("Host", value="localhost")
        config["port"] = st.number_input("Port", value=default_port, step=1)
        config["database"] = st.text_input("Database name")
        config["user"] = st.text_input("Username")
        config["password"] = st.text_input("Password", type="password")

    connect_btn = st.button("Connect", type="primary", use_container_width=True)

    if connect_btn:
        ConnectorClass = CONNECTOR_MAP[db_type]
        connector = ConnectorClass(config)
        with st.spinner("Testing connection..."):
            ok, msg = connector.test_connection()
        if ok:
            connector.connect()
            schema = connector.get_schema()
            st.session_state["connector"] = connector
            st.session_state["schema"] = schema
            st.session_state["db_label"] = f"{db_type}"
            st.session_state["messages"] = []
            st.success(msg)
        else:
            st.error(msg)

    # Schema expander
    if "schema" in st.session_state and st.session_state["schema"]:
        with st.expander("Schema", expanded=False):
            for table, cols in st.session_state["schema"].items():
                st.markdown(f"**{table}**")
                for col in cols:
                    st.markdown(f"  - `{col}`")

# ── Main area ─────────────────────────────────────────────────────────────────
if "connector" not in st.session_state:
    st.info("Connect to a data source using the sidebar to get started.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Example question buttons
example_questions = [
    "How many rows are in each table?",
    "Show me the first 10 rows of the largest table.",
    "Are there any null values in my data?",
    "Detect anomalies across all tables.",
]

cols = st.columns(len(example_questions))
for col, question in zip(cols, example_questions):
    if col.button(question, use_container_width=True):
        st.session_state["pending_question"] = question

# Chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Resolve pending question from example buttons
user_input = st.chat_input("Ask anything about your data...")
if "pending_question" in st.session_state:
    user_input = st.session_state.pop("pending_question")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status_placeholder = st.empty()

        def on_tool_call(tool_name: str, tool_input: dict) -> None:
            if tool_name == "query_database":
                status_placeholder.info(f"Running SQL: `{tool_input.get('sql', '')[:120]}`")
            elif tool_name == "detect_anomalies":
                col_info = f".`{tool_input['column']}`" if tool_input.get("column") else ""
                status_placeholder.info(
                    f"Analyzing `{tool_input['table']}`{col_info} for anomalies..."
                )

        with st.spinner("Thinking..."):
            response = agent_turn(
                connector=st.session_state["connector"],
                schema=st.session_state["schema"],
                db_label=st.session_state["db_label"],
                user_message=user_input,
                on_tool_call=on_tool_call,
            )

        status_placeholder.empty()
        st.markdown(response)

    st.session_state["messages"].append({"role": "assistant", "content": response})
