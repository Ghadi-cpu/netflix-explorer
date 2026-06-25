"""
🎬 NETFLIX CONTENT EXPLORER — Streamlit Dashboard
A polished, Netflix-branded interactive dashboard built on the cleaned
movies dataset from Movies_netflix.ipynb.

Run with:  streamlit run app.py
"""
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Netflix Content Explorer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Netflix palette
NF_RED = "#E50914"
NF_DARK = "#141414"
NF_DARK2 = "#1f1f1f"
NF_GREY = "#808080"
NF_LIGHT = "#f5f5f1"
ACCENT_SEQ = ["#E50914", "#ff6b6b", "#f5b14c", "#ffd76b",
              "#b81d24", "#831010", "#ff9f1c", "#e2c044"]

# ----------------------------------------------------------------------------
# CUSTOM CSS — make it look NOT boring
# ----------------------------------------------------------------------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;600;700;900&display=swap');

    /* App background */
    .stApp {{
        background: radial-gradient(ellipse at top, #1a1a1a 0%, {NF_DARK} 55%, #000 100%);
        color: {NF_LIGHT};
    }}
    /* Hide default header/footer */
    #MainMenu, footer, header {{visibility: hidden;}}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #000 0%, #141414 100%);
        border-right: 1px solid rgba(229,9,20,0.35);
    }}
    section[data-testid="stSidebar"] * {{ color: {NF_LIGHT}; }}

    /* Headings font */
    h1, h2, h3 {{ font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }}

    .netflix-logo {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.6rem;
        color: {NF_RED};
        letter-spacing: 2px;
        text-shadow: 0 0 18px rgba(229,9,20,0.55);
        margin: 0; line-height: 1;
    }}
    .netflix-sub {{
        font-family: 'Inter', sans-serif;
        font-weight: 300; color: {NF_GREY};
        font-size: 1.05rem; margin-top: -4px;
    }}

    /* Metric cards */
    .metric-card {{
        background: linear-gradient(145deg, #1f1f1f, #2b2b2b);
        border: 1px solid rgba(229,9,20,0.25);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 6px 22px rgba(0,0,0,0.6);
        transition: transform .2s ease, box-shadow .2s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 10px 30px rgba(229,9,20,0.35);
        border-color: {NF_RED};
    }}
    .metric-value {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.6rem; color: {NF_RED}; line-height: 1;
    }}
    .metric-label {{
        color: {NF_GREY}; font-size: .8rem;
        text-transform: uppercase; letter-spacing: 1.5px;
    }}

    /* Section title with red bar */
    .section-title {{
        font-family: 'Inter', sans-serif; font-weight: 700;
        font-size: 1.4rem; margin: 8px 0 4px 0;
        border-left: 5px solid {NF_RED}; padding-left: 12px;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        background: #1f1f1f; border-radius: 8px 8px 0 0;
        padding: 8px 18px; color: {NF_GREY};
    }}
    .stTabs [aria-selected="true"] {{
        background: {NF_RED} !important; color: white !important;
    }}

    /* Dataframe tweak */
    .stDataFrame {{ border-radius: 12px; overflow: hidden; }}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# DATA LOADING + CLEANING (mirrors the notebook pipeline)
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    here = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(here, "movies.csv"))

    # drop duplicate movie ids (notebook step)
    df = df.drop_duplicates(subset="movie_id").reset_index(drop=True)

    df["is_netflix_original"] = df["is_netflix_original"].astype(int)
    df["content_warning"] = df["content_warning"].astype(int)

    # engineered features from the notebook
    df["decade"] = (df["release_year"] // 10) * 10
    df["duration_band"] = pd.cut(
        df["duration_minutes"],
        bins=[-1, 30, 60, 120, 1000],
        labels=["short", "medium", "feature", "long"],
    )
    return df


df = load_data()

# ----------------------------------------------------------------------------
# SIDEBAR — FILTERS
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<div class='netflix-logo'>NETFLIX</div>", unsafe_allow_html=True)
    st.markdown("<div class='netflix-sub'>Content Explorer</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🎛️ Filters")

    yr_min, yr_max = int(df.release_year.min()), int(df.release_year.max())
    year_range = st.slider("📅 Release Year", yr_min, yr_max, (yr_min, yr_max))

    langs = sorted(df.language.unique())
    sel_langs = st.multiselect("🌐 Language", langs, default=langs)

    genres = sorted(df.genre_primary.unique())
    sel_genres = st.multiselect("🎭 Genre", genres, default=genres)

    ctypes = sorted(df.content_type.unique())
    sel_ctypes = st.multiselect("📺 Content Type", ctypes, default=ctypes)

    ratings_order = ["TV-Y", "TV-Y7", "TV-G", "TV-PG", "TV-14", "TV-MA",
                     "G", "PG", "PG-13", "R", "NC-17"]
    avail_ratings = [r for r in ratings_order if r in df.rating.unique()]
    sel_ratings = st.multiselect("🔞 Rating", avail_ratings, default=avail_ratings)

    st.markdown("##### Quick toggles")
    only_originals = st.toggle("Netflix Originals only ⭐")
    only_warning = st.toggle("Has content warning ⚠️")

    st.markdown("---")
    st.caption("Built from Movies_netflix.ipynb")

# Apply filters
mask = (
    df.release_year.between(*year_range)
    & df.language.isin(sel_langs)
    & df.genre_primary.isin(sel_genres)
    & df.content_type.isin(sel_ctypes)
    & df.rating.isin(sel_ratings)
)
if only_originals:
    mask &= df.is_netflix_original == 1
if only_warning:
    mask &= df.content_warning == 1

fdf = df[mask].copy()

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
c1, c2 = st.columns([0.7, 0.3])
with c1:
    st.markdown(
        f"<div class='netflix-logo' style='font-size:4.5rem'>NETFLIX</div>"
        f"<div class='netflix-sub'>Explore the catalog · {len(df):,} titles · interactive analytics</div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Empty-state guard
if fdf.empty:
    st.warning("No titles match your filters. Try widening your selection on the left.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------------------------
def metric_card(label, value):
    return (
        f"<div class='metric-card'>"
        f"<div class='metric-value'>{value}</div>"
        f"<div class='metric-label'>{label}</div></div>"
    )

k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(metric_card("Titles", f"{len(fdf):,}"), unsafe_allow_html=True)
k2.markdown(metric_card("Netflix Originals", f"{int(fdf.is_netflix_original.sum()):,}"),
            unsafe_allow_html=True)
avg_imdb = fdf.imdb_rating.mean()
k3.markdown(metric_card("Avg IMDb", f"{avg_imdb:.1f}" if not np.isnan(avg_imdb) else "—"),
            unsafe_allow_html=True)
k4.markdown(metric_card("Languages", f"{fdf.language.nunique()}"), unsafe_allow_html=True)
k5.markdown(metric_card("Avg Duration", f"{fdf.duration_minutes.mean():.0f}m"),
            unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# PLOTLY THEME HELPER
# ----------------------------------------------------------------------------
def style_fig(fig, h=380):
    fig.update_layout(
        title=None,                       # remove the stray "undefined" title
        height=h,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=NF_LIGHT, family="Inter"),
        margin=dict(l=10, r=10, t=20, b=10),
        title_font=dict(size=16, color=NF_LIGHT),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    return fig


# ----------------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊  Overview", "🎭  Genres & Ratings", "🌍  Global", "📋  Browse Titles"]
)

# ---- TAB 1: OVERVIEW --------------------------------------------------------
with tab1:
    cc1, cc2 = st.columns(2)

    with cc1:
        st.markdown("<div class='section-title'>Titles by Decade</div>",
                    unsafe_allow_html=True)
        dec = fdf.groupby("decade").size().reset_index(name="count")
        fig = px.bar(dec, x="decade", y="count", text="count",
                     color="count", color_continuous_scale=["#831010", NF_RED, "#ff9f1c"])
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with cc2:
        st.markdown("<div class='section-title'>Content Type Mix</div>",
                    unsafe_allow_html=True)
        ct = fdf.content_type.value_counts().reset_index()
        ct.columns = ["content_type", "count"]
        fig = px.pie(ct, names="content_type", values="count", hole=0.55,
                     color_discrete_sequence=ACCENT_SEQ)
        fig.update_traces(textinfo="percent+label",
                          marker=dict(line=dict(color=NF_DARK, width=2)))
        st.plotly_chart(style_fig(fig), use_container_width=True)

    cc3, cc4 = st.columns(2)
    with cc3:
        st.markdown("<div class='section-title'>Duration Bands</div>",
                    unsafe_allow_html=True)
        order = ["short", "medium", "feature", "long"]
        db = fdf.duration_band.value_counts().reindex(order).reset_index()
        db.columns = ["band", "count"]
        fig = px.bar(db, x="band", y="count", text="count",
                     color="band", color_discrete_sequence=ACCENT_SEQ)
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with cc4:
        st.markdown("<div class='section-title'>Originals vs. Licensed</div>",
                    unsafe_allow_html=True)
        orig = fdf.is_netflix_original.map({1: "Netflix Original", 0: "Licensed"}) \
                  .value_counts().reset_index()
        orig.columns = ["kind", "count"]
        fig = px.pie(orig, names="kind", values="count", hole=0.55,
                     color_discrete_sequence=[NF_RED, "#444"])
        fig.update_traces(textinfo="percent+label",
                          marker=dict(line=dict(color=NF_DARK, width=2)))
        st.plotly_chart(style_fig(fig), use_container_width=True)

# ---- TAB 2: GENRES & RATINGS ------------------------------------------------
with tab2:
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("<div class='section-title'>Top Genres</div>",
                    unsafe_allow_html=True)
        g = fdf.genre_primary.value_counts().head(12).reset_index()
        g.columns = ["genre", "count"]
        fig = px.bar(g, x="count", y="genre", orientation="h", text="count",
                     color="count", color_continuous_scale=["#831010", NF_RED, "#ffd76b"])
        fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        fig.update_traces(textposition="outside")
        st.plotly_chart(style_fig(fig, h=430), use_container_width=True)

    with cc2:
        st.markdown("<div class='section-title'>Content by Rating</div>",
                    unsafe_allow_html=True)
        r = fdf.rating.value_counts().reset_index()
        r.columns = ["rating", "count"]
        fig = px.bar(r, x="rating", y="count", text="count",
                     color="count", color_continuous_scale=["#831010", NF_RED, "#ff9f1c"])
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig, h=430), use_container_width=True)

    st.markdown("<div class='section-title'>IMDb Rating Distribution</div>",
                unsafe_allow_html=True)
    imdb_data = fdf.dropna(subset=["imdb_rating"])
    if not imdb_data.empty:
        fig = px.histogram(imdb_data, x="imdb_rating", nbins=30,
                           color_discrete_sequence=[NF_RED])
        fig.update_traces(marker_line_color=NF_DARK, marker_line_width=1)
        st.plotly_chart(style_fig(fig, h=320), use_container_width=True)
    else:
        st.info("No IMDb ratings available for the current filters.")

# ---- TAB 3: GLOBAL ----------------------------------------------------------
with tab3:
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("<div class='section-title'>Titles by Language</div>",
                    unsafe_allow_html=True)
        lng = fdf.language.value_counts().reset_index()
        lng.columns = ["language", "count"]
        fig = px.bar(lng, x="language", y="count", text="count",
                     color="count", color_continuous_scale=["#831010", NF_RED, "#ffd76b"])
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with cc2:
        st.markdown("<div class='section-title'>Country of Origin</div>",
                    unsafe_allow_html=True)
        cmap = {"USA": "United States", "UK": "United Kingdom",
                "South Korea": "South Korea", "Japan": "Japan",
                "France": "France", "Germany": "Germany",
                "Spain": "Spain", "India": "India"}
        cn = fdf.country_of_origin.value_counts().reset_index()
        cn.columns = ["country", "count"]
        cn["country_full"] = cn["country"].map(cmap).fillna(cn["country"])
        fig = px.choropleth(cn, locations="country_full", locationmode="country names",
                            color="count", color_continuous_scale=["#3a0a0c", NF_RED, "#ffd76b"])
        fig.update_geos(bgcolor="rgba(0,0,0,0)", showframe=False,
                        showcoastlines=False, projection_type="natural earth",
                        landcolor="#222")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    st.markdown("<div class='section-title'>Genre Popularity Across Decades</div>",
                unsafe_allow_html=True)
    top_g = fdf.genre_primary.value_counts().head(8).index
    heat = (fdf[fdf.genre_primary.isin(top_g)]
            .groupby(["decade", "genre_primary"]).size().reset_index(name="count"))
    if not heat.empty:
        pivot = heat.pivot(index="genre_primary", columns="decade", values="count").fillna(0)
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values, x=pivot.columns.astype(str), y=pivot.index,
            colorscale=[[0, "#1a1a1a"], [0.5, NF_RED], [1, "#ffd76b"]],
            hovertemplate="Decade %{x}<br>%{y}<br>Count: %{z}<extra></extra>"))
        st.plotly_chart(style_fig(fig, h=360), use_container_width=True)

# ---- TAB 4: BROWSE ----------------------------------------------------------
with tab4:
    st.markdown("<div class='section-title'>Browse the catalog</div>",
                unsafe_allow_html=True)
    search = st.text_input("🔎 Search by title", "")
    show = fdf.copy()
    if search:
        show = show[show.title.str.contains(search, case=False, na=False)]

    sort_col = st.selectbox("Sort by",
                            ["imdb_rating", "release_year", "duration_minutes", "title"])
    show = show.sort_values(sort_col, ascending=(sort_col == "title"), na_position="last")

    display_cols = ["title", "content_type", "genre_primary", "release_year",
                    "rating", "language", "country_of_origin", "imdb_rating",
                    "duration_minutes", "is_netflix_original"]
    show_disp = show[display_cols].rename(columns={
        "title": "Title", "content_type": "Type", "genre_primary": "Genre",
        "release_year": "Year", "rating": "Rating", "language": "Language",
        "country_of_origin": "Country", "imdb_rating": "IMDb",
        "duration_minutes": "Min", "is_netflix_original": "Original"})
    show_disp["Original"] = show_disp["Original"].map({1: "⭐", 0: ""})

    st.dataframe(show_disp, use_container_width=True, height=480, hide_index=True)
    st.caption(f"Showing {len(show):,} of {len(df):,} titles")

    csv = show.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data (CSV)", csv,
                       "netflix_filtered.csv", "text/csv")

# Footer
st.markdown(
    f"<br><hr style='border-color:rgba(229,9,20,0.2)'>"
    f"<div style='text-align:center;color:{NF_GREY};font-size:.8rem'>"
    f"🎬 Netflix Content Explorer — interactive dashboard · data from Movies_netflix.ipynb"
    f"</div>", unsafe_allow_html=True)
