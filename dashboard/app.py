
import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
import unicodedata
import re
from pathlib import Path


# ============================================================
# 1. CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Trivial Pursuit | Benchmark IA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DB_FILE = BASE_DIR / "gold" / "warehouse.duckdb"


# ============================================================
# 2. COULEURS - DESIGN ORIGINAL
# ============================================================

BG = "#0B1020"
SIDEBAR = "#11182B"
CARD = "#151B32"
BORDER = "#293451"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"

BLUE = "#38BDF8"
PURPLE = "#8B5CF6"
GREEN = "#34D399"
YELLOW = "#FBBF24"


# ============================================================
# 3. STYLE CSS - DESIGN ORIGINAL
# ============================================================

st.markdown(f"""
<style>

.stApp {{
    background-color: {BG};
    color: {TEXT};
}}

.block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
}}

h1, h2, h3 {{
    color: {TEXT} !important;
}}

[data-testid="stSidebar"] {{
    background-color: {SIDEBAR};
    border-right: 1px solid {BORDER};
}}

[data-testid="stMetric"] {{
    background-color: {CARD};
    padding: 18px;
    border-radius: 10px;
    border: 1px solid {BORDER};
}}

[data-testid="stMetricLabel"] {{
    color: {MUTED} !important;
}}

[data-testid="stMetricValue"] {{
    color: {TEXT} !important;
}}

[data-testid="stPlotlyChart"] {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 8px;
}}

hr {{
    border-color: {BORDER};
}}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 4. NORMALISATION DES NOMS DE COLONNES
# ============================================================

def normalize_name(name):

    name = str(name).strip().lower()

    name = unicodedata.normalize("NFKD", name)

    name = "".join(
        char for char in name
        if not unicodedata.combining(char)
    )

    name = re.sub(r"[^a-z0-9]+", "_", name)

    return name.strip("_")


# Noms possibles dans le warehouse.
# Les noms normalisés permettent aussi de gérer les accents.

COLUMN_ALIASES = {

    "question": [
        "question",
        "texte_question",
        "libelle_question",
        "enonce",
        "question_text"
    ],

    "ai_model": [
        "ai_model",
        "model_name",
        "nom_du_modele",
        "nom_modele",
        "modele",
        "nom_du_model",
        "model"
    ],

    "ai_correct": [
        "ai_correct",
        "is_correct",
        "correct",
        "reponse_correcte",
        "est_correcte",
        "est_correct",
        "correct_answer_flag",
        "resultat",
        "is_answer_correct"
    ],

    "response_time": [
        "response_time",
        "temps_reponse",
        "temps_de_reponse",
        "temps_moyen_reponse",
        "duree_reponse",
        "execution_time",
        "latence",
        "latency"
    ],

    "category": [
        "category",
        "categorie",
        "nom_categorie",
        "categorie_question",
        "type_question",
        "domaine",
        "theme"
    ],

    "source": [
        "source",
        "origine",
        "source_donnees",
        "jeu_donnees"
    ]

}


# ============================================================
# 5. CONNEXION AU WAREHOUSE
# ============================================================

@st.cache_data
def get_warehouse_relations(db_path, db_mtime):

    con = duckdb.connect(db_path, read_only=True)

    try:

        return con.execute("""
            SELECT
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN (
                'information_schema',
                'pg_catalog'
            )
            ORDER BY table_schema, table_name
        """).df()

    finally:

        con.close()


@st.cache_data
def get_relation_columns(
    db_path,
    schema,
    table,
    db_mtime
):

    con = duckdb.connect(db_path, read_only=True)

    try:

        return con.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = ?
              AND table_name = ?
            ORDER BY ordinal_position
        """, [schema, table]).df()["column_name"].tolist()

    finally:

        con.close()


@st.cache_data
def read_relation(
    db_path,
    schema,
    table,
    db_mtime
):

    con = duckdb.connect(db_path, read_only=True)

    try:

        safe_schema = schema.replace('"', '""')
        safe_table = table.replace('"', '""')

        query = f'''
            SELECT *
            FROM "{safe_schema}"."{safe_table}"
        '''

        return con.execute(query).df()

    finally:

        con.close()


# ============================================================
# 6. DETECTION AUTOMATIQUE DES COLONNES
# ============================================================

def detect_columns(columns):

    normalized_columns = {
        normalize_name(column): column
        for column in columns
    }

    mapping = {}

    for target, aliases in COLUMN_ALIASES.items():

        for alias in aliases:

            if alias in normalized_columns:

                mapping[target] = normalized_columns[alias]
                break

    return mapping


# ============================================================
# 7. DETECTION AUTOMATIQUE DE LA TABLE DE BENCHMARK
# ============================================================

def find_best_relation(relations, db_path, db_mtime):

    candidates = []

    for row in relations.itertuples(index=False):

        schema = row.table_schema
        table = row.table_name

        columns = get_relation_columns(
            db_path,
            schema,
            table,
            db_mtime
        )

        mapping = detect_columns(columns)

        # Colonnes indispensables pour le dashboard
        required = [
            "question",
            "ai_model",
            "ai_correct",
            "response_time",
            "category"
        ]

        score = sum(
            column in mapping
            for column in required
        )

        # La source est facultative
        if "source" in mapping:
            score += 1

        candidates.append({
            "schema": schema,
            "table": table,
            "mapping": mapping,
            "score": score
        })

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    best = candidates[0]

    if best["score"] < 5:
        return None

    return best


# ============================================================
# 8. CONVERSION DES RESULTATS
# ============================================================

def convert_correctness(value):

    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):

        if value == 1:
            return True

        if value == 0:
            return False

        return None

    value = normalize_name(value)

    true_values = [
        "true",
        "1",
        "oui",
        "yes",
        "vrai",
        "correct",
        "correcte",
        "bonne_reponse",
        "reponse_correcte"
    ]

    false_values = [
        "false",
        "0",
        "non",
        "no",
        "faux",
        "incorrect",
        "incorrecte",
        "mauvaise_reponse"
    ]

    if value in true_values:
        return True

    if value in false_values:
        return False

    return None


# ============================================================
# 9. PREPARATION DES DONNEES DU WAREHOUSE
# ============================================================

def prepare_data(raw_df, mapping):

    df = pd.DataFrame()

    # Correspondance entre les colonnes du warehouse
    # et les noms utilisés par le dashboard.

    for target, original in mapping.items():

        df[target] = raw_df[original]

    # Source facultative

    if "source" not in df.columns:

        df["source"] = "Warehouse"

    df["source"] = (
        df["source"]
        .fillna("Non renseignée")
        .astype(str)
    )

    # Modèle

    df["ai_model"] = (
        df["ai_model"]
        .fillna("Modèle inconnu")
        .astype(str)
    )

    # Catégorie

    df["category"] = (
        df["category"]
        .fillna("Non renseignée")
        .astype(str)
    )

    # Question

    df["question"] = (
        df["question"]
        .fillna("")
        .astype(str)
    )

    # Résultat de l'évaluation

    df["ai_correct"] = (
        df["ai_correct"]
        .apply(convert_correctness)
    )

    # Temps de réponse

    df["response_time"] = pd.to_numeric(
        df["response_time"],
        errors="coerce"
    )

    return df


# ============================================================
# 10. FONCTION STYLE DES GRAPHIQUES
# ============================================================

def apply_chart_style(fig):

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(
            color=TEXT,
            family="Arial"
        ),
        margin=dict(
            l=30,
            r=25,
            t=60,
            b=35
        ),
        legend_title_text="Source"
    )

    fig.update_xaxes(
        gridcolor=BORDER,
        zerolinecolor=BORDER
    )

    fig.update_yaxes(
        gridcolor=BORDER,
        zerolinecolor=BORDER
    )

    return fig


# ============================================================
# 11. VERIFICATION DU WAREHOUSE
# ============================================================

if not DB_FILE.exists():

    st.error(
        "Impossible de trouver le warehouse DuckDB."
    )

    st.stop()


try:

    db_mtime = DB_FILE.stat().st_mtime

    relations = get_warehouse_relations(
        str(DB_FILE),
        db_mtime
    )

    best_relation = find_best_relation(
        relations,
        str(DB_FILE),
        db_mtime
    )

except Exception as error:

    st.error(
        f"Erreur lors de la lecture du warehouse : {error}"
    )

    st.stop()


if best_relation is None:

    st.error(
        "Aucune table ou vue du warehouse ne contient "
        "toutes les informations nécessaires au benchmark."
    )

    st.info(
        "Il faut identifier les tables contenant les questions, "
        "les modèles, les résultats, les temps de réponse "
        "et les catégories."
    )

    st.stop()


# ============================================================
# 12. CHARGEMENT DE LA TABLE IDENTIFIEE
# ============================================================

try:

    raw_df = read_relation(
        str(DB_FILE),
        best_relation["schema"],
        best_relation["table"],
        db_mtime
    )

    df = prepare_data(
        raw_df,
        best_relation["mapping"]
    )

except Exception as error:

    st.error(
        f"Erreur lors du traitement des données : {error}"
    )

    st.stop()


if df.empty:

    st.warning(
        "Aucune donnée disponible dans le warehouse."
    )

    st.stop()


# ============================================================
# 13. MENU LATERAL - DESIGN ORIGINAL
# ============================================================

st.sidebar.title("TRIVIAL PURSUIT")

st.sidebar.caption("TABLEAU DE BORD IA")

st.sidebar.divider()

st.sidebar.subheader("Navigation")

page = st.sidebar.radio(
    "Navigation",
    [
        "Vue générale",
        "Comparaison des modèles",
        "Analyse par catégorie",
        "Données"
    ],
    label_visibility="collapsed"
)

st.sidebar.divider()

st.sidebar.subheader("Filtres")

sources = sorted(
    df["source"].dropna().unique().tolist()
)

models = sorted(
    df["ai_model"].dropna().unique().tolist()
)

selected_sources = st.sidebar.multiselect(
    "Source",
    sources,
    default=sources
)

selected_models = st.sidebar.multiselect(
    "Modèle d'intelligence artificielle",
    models,
    default=models
)

st.sidebar.divider()

st.sidebar.caption(
    "Projet Data Engineering · 2026/2027"
)


# ============================================================
# 14. APPLICATION DES FILTRES
# ============================================================

filtered_df = df[
    df["source"].isin(selected_sources)
    & df["ai_model"].isin(selected_models)
].copy()


if filtered_df.empty:

    st.warning(
        "Aucune donnée disponible avec ces filtres."
    )

    st.stop()


# ============================================================
# 15. CALCUL DES INDICATEURS
# ============================================================

evaluated_df = filtered_df.dropna(
    subset=["ai_correct"]
).copy()

total_questions = len(filtered_df)

total_evaluations = len(evaluated_df)

correct_answers = int(
    (evaluated_df["ai_correct"] == True).sum()
)

incorrect_answers = int(
    (evaluated_df["ai_correct"] == False).sum()
)

accuracy = (
    correct_answers / total_evaluations * 100
    if total_evaluations > 0 else 0
)

avg_response_time = filtered_df[
    "response_time"
].mean()

total_models = filtered_df[
    "ai_model"
].nunique()


# ============================================================
# 16. STATISTIQUES PAR MODELE ET SOURCE
# ============================================================

stats = (
    filtered_df
    .groupby(["source", "ai_model"])
    .agg(
        total_questions=("question", "count"),
        evaluated_questions=("ai_correct", "count"),
        correct_answers=("ai_correct", "sum"),
        avg_response_time=("response_time", "mean")
    )
    .reset_index()
)

stats["accuracy"] = (
    stats["correct_answers"]
    / stats["evaluated_questions"].replace(
        0, float("nan")
    )
    * 100
)

stats["error_rate"] = 100 - stats["accuracy"]


# ============================================================
# 17. STATISTIQUES PAR CATEGORIE
# ============================================================

evaluated_categories = evaluated_df.dropna(
    subset=["category"]
).copy()

category_stats = (
    evaluated_categories
    .groupby(["source", "ai_model", "category"])
    .agg(
        total_questions=("ai_correct", "count"),
        accuracy=("ai_correct", "mean"),
        avg_response_time=("response_time", "mean")
    )
    .reset_index()
)

category_stats["accuracy"] *= 100


# ============================================================
# 18. EN-TETE COMMUN
# ============================================================

st.caption("TRIVIAL PURSUIT / BENCHMARK IA")


# ============================================================
# 19. PAGE VUE GENERALE
# ============================================================

if page == "Vue générale":

    st.title("Vue générale")

    st.caption(
        "Synthèse des performances des modèles "
        "d'intelligence artificielle."
    )

    st.divider()

    st.subheader("Indicateurs clés")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Questions",
        f"{total_questions:,}"
    )

    c2.metric(
        "Précision globale",
        f"{accuracy:.2f}%"
    )

    c3.metric(
        "Évaluations",
        f"{total_evaluations:,}"
    )

    c4.metric(
        "Temps moyen",
        f"{avg_response_time:.2f} s"
        if pd.notna(avg_response_time)
        else "N/A"
    )

    c5.metric(
        "Modèles",
        total_models
    )

    st.divider()

    st.subheader("Comparaison des performances")

    col1, col2 = st.columns(2)

    with col1:

        fig = px.bar(
            stats,
            x="ai_model",
            y="accuracy",
            color="source",
            barmode="group",
            title="Précision des modèles (%)",
            color_discrete_sequence=[
                BLUE,
                PURPLE,
                GREEN
            ]
        )

        fig.update_layout(
            yaxis_range=[0, 100],
            xaxis_title="Modèle",
            yaxis_title="Précision (%)"
        )

        st.plotly_chart(
            apply_chart_style(fig),
            use_container_width=True
        )

    with col2:

        fig = px.bar(
            stats,
            x="ai_model",
            y="avg_response_time",
            color="source",
            barmode="group",
            title="Temps moyen de réponse",
            color_discrete_sequence=[
                YELLOW,
                PURPLE,
                BLUE
            ]
        )

        fig.update_layout(
            xaxis_title="Modèle",
            yaxis_title="Temps (secondes)"
        )

        st.plotly_chart(
            apply_chart_style(fig),
            use_container_width=True
        )

    st.divider()

    st.subheader("Performance par catégorie")

    if not category_stats.empty:

        fig = px.bar(
            category_stats,
            x="category",
            y="accuracy",
            color="ai_model",
            barmode="group",
            title="Précision par catégorie (%)",
            color_discrete_sequence=[
                BLUE,
                PURPLE,
                GREEN
            ]
        )

        fig.update_layout(
            yaxis_range=[0, 100],
            xaxis_title="Catégorie",
            yaxis_title="Précision (%)"
        )

        st.plotly_chart(
            apply_chart_style(fig),
            use_container_width=True
        )

    else:

        st.info(
            "Aucune donnée disponible pour les catégories."
        )


# ============================================================
# 20. PAGE COMPARAISON DES MODELES
# ============================================================

elif page == "Comparaison des modèles":

    st.title("Comparaison des modèles")

    st.caption(
        "Analyse comparative de la précision "
        "et de la rapidité."
    )

    st.divider()

    st.subheader("Précision des modèles")

    fig = px.bar(
        stats,
        x="ai_model",
        y="accuracy",
        color="source",
        barmode="group",
        text_auto=".2f",
        color_discrete_sequence=[
            BLUE,
            PURPLE,
            GREEN
        ]
    )

    fig.update_layout(
        yaxis_range=[0, 100],
        xaxis_title="Modèle",
        yaxis_title="Précision (%)"
    )

    st.plotly_chart(
        apply_chart_style(fig),
        use_container_width=True
    )

    st.divider()

    st.subheader("Temps de réponse")

    fig = px.bar(
        stats,
        x="ai_model",
        y="avg_response_time",
        color="source",
        barmode="group",
        text_auto=".2f",
        color_discrete_sequence=[
            YELLOW,
            PURPLE,
            BLUE
        ]
    )

    fig.update_layout(
        xaxis_title="Modèle",
        yaxis_title="Temps moyen (secondes)"
    )

    st.plotly_chart(
        apply_chart_style(fig),
        use_container_width=True
    )

    st.divider()

    st.subheader("Tableau comparatif")

    comparison = stats[
        [
            "source",
            "ai_model",
            "total_questions",
            "accuracy",
            "error_rate",
            "avg_response_time"
        ]
    ].copy()

    comparison.columns = [
        "Source",
        "Modèle",
        "Questions",
        "Précision (%)",
        "Taux d'erreur (%)",
        "Temps moyen (s)"
    ]

    st.dataframe(
        comparison.style.format({
            "Précision (%)": "{:.2f}",
            "Taux d'erreur (%)": "{:.2f}",
            "Temps moyen (s)": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 21. PAGE ANALYSE PAR CATEGORIE
# ============================================================

elif page == "Analyse par catégorie":

    st.title("Analyse par catégorie")

    st.caption(
        "Étude des performances selon les domaines "
        "de connaissance."
    )

    st.divider()

    if not category_stats.empty:

        st.subheader("Précision par catégorie")

        fig = px.bar(
            category_stats,
            x="category",
            y="accuracy",
            color="ai_model",
            barmode="group",
            color_discrete_sequence=[
                BLUE,
                PURPLE,
                GREEN
            ]
        )

        fig.update_layout(
            yaxis_range=[0, 100],
            xaxis_title="Catégorie",
            yaxis_title="Précision (%)"
        )

        st.plotly_chart(
            apply_chart_style(fig),
            use_container_width=True
        )

        st.divider()

        st.subheader("Temps moyen par catégorie")

        fig = px.bar(
            category_stats,
            x="category",
            y="avg_response_time",
            color="ai_model",
            barmode="group",
            color_discrete_sequence=[
                YELLOW,
                PURPLE,
                BLUE
            ]
        )

        fig.update_layout(
            xaxis_title="Catégorie",
            yaxis_title="Temps moyen (secondes)"
        )

        st.plotly_chart(
            apply_chart_style(fig),
            use_container_width=True
        )

        st.divider()

        st.subheader("Classement des catégories")

        ranking = (
            category_stats
            .groupby("category")
            .agg(
                accuracy=("accuracy", "mean"),
                questions=("total_questions", "sum"),
                avg_response_time=(
                    "avg_response_time", "mean"
                )
            )
            .sort_values(
                "accuracy",
                ascending=False
            )
            .reset_index()
        )

        ranking.columns = [
            "Catégorie",
            "Précision moyenne (%)",
            "Questions évaluées",
            "Temps moyen (s)"
        ]

        st.dataframe(
            ranking.style.format({
                "Précision moyenne (%)": "{:.2f}",
                "Temps moyen (s)": "{:.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )

        if not ranking.empty:

            c1, c2 = st.columns(2)

            c1.metric(
                "Catégorie la mieux maîtrisée",
                ranking.iloc[0]["Catégorie"],
                f"{ranking.iloc[0]['Précision moyenne (%)']:.2f}%"
            )

            c2.metric(
                "Catégorie la plus difficile",
                ranking.iloc[-1]["Catégorie"],
                f"{ranking.iloc[-1]['Précision moyenne (%)']:.2f}%"
            )

    else:

        st.info(
            "Aucune donnée disponible pour les catégories."
        )


# ============================================================
# 22. PAGE DONNEES
# ============================================================

elif page == "Données":

    st.title("Données")

    st.caption(
        "Consultation des données utilisées "
        "pour les évaluations."
    )

    st.divider()

    c1, c2 = st.columns(2)

    c1.metric(
        "Nombre de lignes",
        len(filtered_df)
    )

    c2.metric(
        "Nombre de colonnes",
        len(filtered_df.columns)
    )

    st.divider()

    st.subheader("Tableau des évaluations")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

    csv = filtered_df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "Télécharger les données CSV",
        data=csv,
        file_name="trivial_pursuit_benchmark.csv",
        mime="text/csv"
    )


# ============================================================
# 23. PIED DE PAGE
# ============================================================

st.divider()

st.caption(
    "Trivial Pursuit | Benchmark IA | "
    "Projet Data Engineering 2026/2027"
)
