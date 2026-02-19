import os
import json
import time
import logging
import threading

import dash
from dash import dcc, html
import gspread
import mysql.connector
import pandas as pd
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials


def load_local_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_local_env()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)


SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "120"))
SYNC_FROM_GOOGLE_SHEETS = os.getenv("SYNC_FROM_GOOGLE_SHEETS", "true").lower() == "true"
DASHBOARD_SOURCE = os.getenv("DASHBOARD_SOURCE", "sql").strip().lower()
DASHBOARD_REFRESH_SECONDS = int(os.getenv("DASHBOARD_REFRESH_SECONDS", "60"))
ENABLE_SOURCE_FALLBACK = os.getenv("ENABLE_SOURCE_FALLBACK", "false").lower() == "true"
MYSQL_CONNECT_TIMEOUT_SECONDS = int(os.getenv("MYSQL_CONNECT_TIMEOUT_SECONDS", "5"))
MYSQL_READ_TIMEOUT_SECONDS = int(os.getenv("MYSQL_READ_TIMEOUT_SECONDS", "15"))
RUN_SYNC_IN_REQUEST = os.getenv("RUN_SYNC_IN_REQUEST", "false").lower() == "true"
DASHBOARD_CACHE_SECONDS = int(os.getenv("DASHBOARD_CACHE_SECONDS", "120"))
PREWARM_CACHE_ON_START = os.getenv("PREWARM_CACHE_ON_START", "true").lower() == "true"
_last_sync_epoch = 0.0
_last_dashboard_epoch = 0.0
_cached_dashboard_children = None
_cache_refresh_in_progress = False
_cache_lock = threading.Lock()


color_discrete = [
    "#0B132B", "#1C2541", "#3A506B", "#5BC0BE", "#6FFFE9",
    "#5E548E", "#9F86C0", "#BE95C4", "#E0B1CB", "#7B2CBF",
    "#C77DFF", "#4895EF", "#4361EE", "#560BAD",
]

COLUMN_ALIASES = {
    "timestamp": ["timestamp", "marca temporal", "time stamp"],
    "play_frequency": ["play_frequency", "play frequency"],
    "platform": ["platform", "plataforma"],
    "genres": ["genres", "genre", "géneros", "generos"],
    "matters_most": ["matters_most", "matters most"],
    "preference": ["preference", "preferencia"],
    "story_importance": ["story_importance", "story importance", "narrative importance"],
    "romance_importance": ["romance_importance", "romance importance"],
    "romance_engagement": ["romance_engagement", "romance engagement"],
    "romance_preference": ["romance_preference", "romance preference"],
    "player_gender": ["player_gender", "player gender"],
    "identity": ["identity", "gender identity"],
    "orientation_importance": ["orientation_importance", "orientation importance"],
    "orientation": ["orientation", "sexual orientation"],
    "inclusive_interest": ["inclusive_interest", "inclusive interest"],
}


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]
    lower_to_actual = {column.lower(): column for column in normalized.columns}

    for canonical, candidates in COLUMN_ALIASES.items():
        existing = lower_to_actual.get(canonical)
        if existing:
            if existing != canonical:
                normalized = normalized.rename(columns={existing: canonical})
            continue

        for candidate in candidates:
            actual = lower_to_actual.get(candidate.lower())
            if actual:
                normalized = normalized.rename(columns={actual: canonical})
                break

    return normalized


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "survey_db"),
        use_pure=True,
        connection_timeout=MYSQL_CONNECT_TIMEOUT_SECONDS,
        read_timeout=MYSQL_READ_TIMEOUT_SECONDS,
    )


def fetch_google_sheet_dataframe() -> pd.DataFrame:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = None
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if service_account_json:
        credentials_dict = json.loads(service_account_json)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    else:
        client_secret_file = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "clientsecret.json")
        credentials = ServiceAccountCredentials.from_json_keyfile_name(client_secret_file, scope)

    client = gspread.authorize(credentials)
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "")
    worksheet_name = os.getenv("GOOGLE_WORKSHEET_NAME", "")

    if not sheet_name:
        raise ValueError("GOOGLE_SHEET_NAME is required for synchronization.")

    spreadsheet = client.open(sheet_name)
    worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.sheet1
    records = worksheet.get_all_records()
    return pd.DataFrame(records)


def sync_google_sheet_to_mysql() -> None:
    global _last_sync_epoch

    if not SYNC_FROM_GOOGLE_SHEETS:
        return

    current_time = time.time()
    if current_time - _last_sync_epoch < SYNC_INTERVAL_SECONDS:
        return

    sheet_df = normalize_dataframe_columns(fetch_google_sheet_dataframe())
    if sheet_df.empty:
        _last_sync_epoch = current_time
        return

    expected_columns = [
        "timestamp",
        "play_frequency",
        "platform",
        "genres",
        "matters_most",
        "preference",
        "story_importance",
        "romance_importance",
        "romance_engagement",
        "romance_preference",
        "player_gender",
        "identity",
        "orientation_importance",
        "orientation",
        "inclusive_interest",
    ]

    source_columns = {column.lower(): column for column in sheet_df.columns}
    normalized_rows = []
    for _, row in sheet_df.iterrows():
        values = []
        for expected_col in expected_columns:
            original_col = source_columns.get(expected_col)
            cell_value = row[original_col] if original_col in row else None
            values.append(None if pd.isna(cell_value) else str(cell_value))
        normalized_rows.append(tuple(values))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT timestamp FROM survey_responses")
        existing_timestamps = {str(item[0]) for item in cursor.fetchall() if item[0] is not None}

        rows_to_insert = [row for row in normalized_rows if row[0] and row[0] not in existing_timestamps]
        if rows_to_insert:
            insert_sql = """
                INSERT INTO survey_responses (
                    timestamp, play_frequency, platform, genres, matters_most, preference,
                    story_importance, romance_importance, romance_engagement, romance_preference,
                    player_gender, identity, orientation_importance, orientation, inclusive_interest
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_sql, rows_to_insert)
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    _last_sync_epoch = current_time


def fetch_data() -> pd.DataFrame:
    def fetch_from_sql() -> pd.DataFrame:
        conn = get_db_connection()
        try:
            return normalize_dataframe_columns(pd.read_sql("SELECT * FROM survey_responses", conn))
        finally:
            conn.close()

    def fetch_from_sheets() -> pd.DataFrame:
        return normalize_dataframe_columns(fetch_google_sheet_dataframe())

    loaders = {
        "sql": fetch_from_sql,
        "sheets": fetch_from_sheets,
    }

    primary = "sql" if DASHBOARD_SOURCE == "sql" else "sheets"
    secondary = "sheets" if primary == "sql" else "sql"
    sources_to_try = (primary, secondary) if ENABLE_SOURCE_FALLBACK else (primary,)

    errors = []
    for source in sources_to_try:
        try:
            df = loaders[source]()
            logger.info("Dashboard data source in use: %s", source)
            return df
        except Exception as exc:
            errors.append(f"{source}: {exc}")
            logger.exception("Failed loading data from %s", source)

    raise RuntimeError("All data sources failed. " + " | ".join(errors))


def apply_figure_style(fig, title_text: str):
    fig.update_layout(
        title={
            "text": f"<b>{title_text}</b>",
            "font": {"family": "Arial", "size": 12, "color": "black"},
            "x": 0.01,
            "xanchor": "left",
        },
        font={"family": "Arial", "size": 9, "color": "black"},
        legend={"font": {"family": "Arial", "size": 9, "color": "black"}},
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"l": 40, "r": 20, "t": 56, "b": 40},
    )
    fig.update_xaxes(
        showgrid=False,
        tickfont={"family": "Arial", "size": 9, "color": "black"},
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#E6E6E6",
        tickfont={"family": "Arial", "size": 9, "color": "black"},
    )
    return fig


def count_bar(df: pd.DataFrame, col: str, title: str, horizontal: bool = False):
    if col not in df.columns:
        fig = px.bar(
            pd.DataFrame({"value": ["No data available"], "count": [0]}),
            x="value",
            y="count",
            color="value",
            color_discrete_sequence=[color_discrete[0]],
        )
        return apply_figure_style(fig, title)

    counts = df[col].fillna("Missing").astype(str).value_counts().reset_index()
    counts.columns = ["value", "count"]

    if horizontal:
        fig = px.bar(
            counts.sort_values("count", ascending=True),
            x="count",
            y="value",
            orientation="h",
            color="value",
            color_discrete_sequence=color_discrete,
        )
    else:
        fig = px.bar(
            counts.sort_values("count", ascending=False),
            x="value",
            y="count",
            color="value",
            color_discrete_sequence=color_discrete,
        )

    return apply_figure_style(fig, title)


app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    style={"backgroundColor": "white", "padding": "16px", "width": "100%", "minHeight": "100vh"},
    children=[
        html.H1(
            "Survey Dashboard",
            style={
                "color": "black",
                "fontFamily": "Arial",
                "fontWeight": "bold",
                "fontSize": "20px",
                "marginBottom": "12px",
            },
        ),
        dcc.Interval(id="refresh-interval", interval=DASHBOARD_REFRESH_SECONDS * 1000, n_intervals=0),
        html.Div(id="dashboard-content"),
    ],
)


def build_dashboard_children(df: pd.DataFrame):
    if df.empty:
        return html.Div(
            "No rows found in the current data source yet.",
            style={"fontFamily": "Arial", "fontSize": "14px", "color": "black", "padding": "12px"},
        )

    drop_cols = {"timestamp", "marca temporal", "id"}
    df = df.loc[:, [c for c in df.columns if c.lower() not in drop_cols]]

    if df.empty or len(df.columns) == 0:
        return html.Div(
            "Data loaded, but no plottable columns were found after normalization.",
            style={"fontFamily": "Arial", "fontSize": "14px", "color": "black", "padding": "12px"},
        )

    def has_usable_data(col: str) -> bool:
        if col not in df.columns:
            return False
        cleaned = (
            df[col]
            .dropna()
            .astype(str)
            .map(lambda value: value.strip())
        )
        cleaned = cleaned[cleaned != ""]
        return not cleaned.empty

    fig_inclusive = count_bar(df, "inclusive_interest", "Interest Due to Inclusive Options")

    if "identity" in df.columns and "player_gender" in df.columns:
        fig_identity = px.histogram(
            df,
            x="identity",
            color="player_gender",
            barmode="group",
            color_discrete_sequence=color_discrete,
        )
        fig_identity = apply_figure_style(fig_identity, "Gender Identity vs. Player Gender Choice")
        fig_identity.update_layout(showlegend=True)
    else:
        fig_identity = count_bar(df, "identity", "Gender Identity vs. Player Gender Choice")

    fig_player_gender = count_bar(df, "player_gender", "Player Gender")

    if "orientation" in df.columns and "orientation_importance" in df.columns:
        fig_orientation = px.histogram(
            df,
            x="orientation",
            color="orientation_importance",
            barmode="group",
            color_discrete_sequence=color_discrete,
        )
        fig_orientation = apply_figure_style(fig_orientation, "Sexual Orientation vs. Importance")
        fig_orientation.update_layout(showlegend=True)
    else:
        fig_orientation = count_bar(df, "orientation", "Sexual Orientation vs. Importance")

    fig_orientation_importance = count_bar(
        df,
        "orientation_importance",
        "Orientation Importance",
    )

    def optimal_graph(col: str):
        title = col.replace("_", " ").title()
        unique_vals = df[col].nunique(dropna=False)
        normalized_col = col.strip().lower()

        if pd.api.types.is_numeric_dtype(df[col]) and unique_vals > 10:
            fig = px.histogram(df, x=col, color_discrete_sequence=color_discrete)
            fig.update_traces(marker_color=color_discrete[2])
            return apply_figure_style(fig, title)

        if unique_vals <= 5:
            return count_bar(df, col, title, horizontal=True)

        fig = count_bar(df, col, title, horizontal=False)
        if (
            normalized_col == "genres"
            or "what games do you enjoy the most" in normalized_col
        ):
            fig.update_xaxes(tickangle=45, automargin=True)
        return fig

    remaining_cols = [
        c
        for c in df.columns
        if c
        not in [
            "inclusive_interest",
            "identity",
            "player_gender",
            "orientation",
            "orientation_importance",
        ]
    ]

    priority_card_items = []
    if has_usable_data("inclusive_interest"):
        priority_card_items.append(
            html.Div([dcc.Graph(figure=fig_inclusive, style={"height": "420px"})], style={"minWidth": "360px"})
        )
    if has_usable_data("identity"):
        priority_card_items.append(
            html.Div([dcc.Graph(figure=fig_identity, style={"height": "420px"})], style={"minWidth": "360px"})
        )
    if has_usable_data("player_gender"):
        priority_card_items.append(
            html.Div([dcc.Graph(figure=fig_player_gender, style={"height": "420px"})], style={"minWidth": "360px"})
        )
    if has_usable_data("orientation"):
        priority_card_items.append(
            html.Div([dcc.Graph(figure=fig_orientation, style={"height": "420px"})], style={"minWidth": "360px"})
        )
    if has_usable_data("orientation_importance"):
        priority_card_items.append(
            html.Div([dcc.Graph(figure=fig_orientation_importance, style={"height": "420px"})], style={"minWidth": "360px"})
        )

    priority_cards = html.Div(
        priority_card_items,
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(420px, 1fr))",
            "gap": "16px",
            "alignItems": "stretch",
        },
    )

    other_graphs = html.Div(
        [
            html.Div([dcc.Graph(figure=optimal_graph(col), style={"height": "360px"})], style={"minWidth": "360px"})
            for col in remaining_cols
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(420px, 1fr))",
            "gap": "16px",
            "marginTop": "16px",
            "alignItems": "stretch",
        },
    )

    sections = []
    if priority_card_items:
        sections.append(priority_cards)
    sections.append(other_graphs)
    return html.Div(sections)


def _get_cached_dashboard():
    with _cache_lock:
        return _cached_dashboard_children, _last_dashboard_epoch


def _set_cached_dashboard(children, timestamp: float) -> None:
    global _cached_dashboard_children, _last_dashboard_epoch
    with _cache_lock:
        _cached_dashboard_children = children
        _last_dashboard_epoch = timestamp


def _refresh_dashboard_cache() -> None:
    global _cache_refresh_in_progress
    try:
        if RUN_SYNC_IN_REQUEST and DASHBOARD_SOURCE == "sql":
            try:
                sync_google_sheet_to_mysql()
            except Exception:
                logger.exception("Google Sheets to MySQL sync failed during background refresh")

        df = fetch_data()
        children = build_dashboard_children(df)
        _set_cached_dashboard(children, time.time())
    except Exception:
        logger.exception("Background dashboard cache refresh failed")
    finally:
        _cache_refresh_in_progress = False


@app.callback(
    dash.dependencies.Output("dashboard-content", "children"),
    [dash.dependencies.Input("refresh-interval", "n_intervals")],
)
def update_dashboard(_n_intervals):
    global _cache_refresh_in_progress

    current_time = time.time()
    cached_dashboard, cached_epoch = _get_cached_dashboard()

    if cached_dashboard is not None:
        cache_age = current_time - cached_epoch
        if cache_age >= DASHBOARD_CACHE_SECONDS and not _cache_refresh_in_progress:
            _cache_refresh_in_progress = True
            threading.Thread(target=_refresh_dashboard_cache, daemon=True).start()
        return cached_dashboard

    try:
        df = fetch_data()
        dashboard_children = build_dashboard_children(df)
        _set_cached_dashboard(dashboard_children, current_time)
        return dashboard_children
    except Exception:
        logger.exception("Failed while preparing initial dashboard")
        return html.Div(
            "Dashboard is online, but data is not available yet. Check GOOGLE_SHEET_NAME, GOOGLE_SERVICE_ACCOUNT_JSON, database connectivity, and Google Sheet sharing permissions.",
            style={"fontFamily": "Arial", "fontSize": "14px", "color": "black", "padding": "12px"},
        )


if PREWARM_CACHE_ON_START:
    _cache_refresh_in_progress = True
    threading.Thread(target=_refresh_dashboard_cache, daemon=True).start()


if __name__ == "__main__":
    app.run_server(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8050")),
        debug=os.getenv("DASH_DEBUG", "false").lower() == "true",
    )
