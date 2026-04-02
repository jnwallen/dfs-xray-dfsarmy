import streamlit as st
import pandas as pd
from collections import Counter
import plotly.express as px
import re
from io import StringIO
import urllib.parse

st.set_page_config(page_title="DFS X-Ray", layout="wide")

# ====================== HEADER ======================
col_l, col_c, col_r = st.columns([1, 3, 1])
with col_l:
    try:
        st.image("JNWLogo.png", width=160)
    except:
        pass
with col_c:
    st.title("DFS X-Ray")
    st.markdown("**Research + Full Lineup Portfolio Analysis**")
with col_r:
    try:
        st.image("blceggLogo.png", width=160)
    except:
        pass

# ====================== FILE UPLOADERS ======================
col1, col2 = st.columns(2)
with col1:
    research_file = st.file_uploader("1. Research Station CSV (required)", type="csv")
with col2:
    lineups_file = st.file_uploader("2. Lineups CSV (optional — enables full X-Ray)", type="csv")

if not research_file:
    st.stop()

# ====================== LOAD RESEARCH ======================
@st.cache_data
def load_research(file):
    df = pd.read_csv(file, header=1)

    def clean_num(val):
        if pd.isna(val):
            return 0.0
        s = str(val).replace('$', '').replace(',', '').replace('%', '').strip()
        try:
            return float(s)
        except:
            return 0.0

    df["Salary"] = df["Salary"].apply(clean_num)
    df["Ownership"] = df["Ownership"].apply(clean_num)
    df["Proj"] = df["Proj"].apply(clean_num)
    df["GPP Target"] = df.get("GPP Target", pd.Series([0] * len(df))).apply(clean_num)
    df["Proj Diff"] = df.get("Proj Diff", pd.Series([0] * len(df))).apply(clean_num)
    df["Dvp"] = df["Dvp"].apply(clean_num)
    df["Rest"] = df.get("Rest", pd.Series([0] * len(df))).apply(clean_num).astype(int)
    df["DFSA Grade"] = df.get("DFSA Grade", pd.Series([0] * len(df))).apply(clean_num)
    df["Pace (+/-)"] = df.get("Pace (+/-)", pd.Series([0] * len(df))).apply(clean_num)
    df["Ceiling"] = df.get("Ceiling", pd.Series([0] * len(df))).apply(clean_num)
    df["USG%"] = df.get("USG%", pd.Series([0] * len(df))).apply(clean_num)

    df["Team"] = df["Team"].astype(str).str.upper().str.strip()
    df["Value_per_k"] = (df["Proj"] / (df["Salary"] / 1000)).round(2)
    df["Points_per_min"] = (df["Proj"] / df["Minutes"]).round(2) if "Minutes" in df.columns and df["Minutes"].max() > 0 else 0.0
    df["Min_Trend"] = df.get("Minutes", pd.Series([0] * len(df))) - df.get("5gMin", pd.Series([0] * len(df)))

    return df

research_df = load_research(research_file)

# ====================== LOAD LINEUPS ======================
lineups_df = None
pos_cols = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']
name_to_info = {}
name_to_team = {}

if lineups_file:
    lines = []
    with lineups_file as f:
        for line in f:
            line_str = line.decode('utf-8').strip()
            if not line_str: continue
            if "Position" in line_str or "Name + ID" in line_str or line_str.count(',') > 15:
                break
            lines.append(line_str)

    clean_csv = "\n".join(lines)
    lineups_df = pd.read_csv(StringIO(clean_csv))

    def extract_name(cell):
        if pd.isna(cell): return None
        cell = str(cell).strip()
        if '(' in cell:
            name_part = cell.split('(')[0].strip()
        else:
            name_part = cell
        return ' '.join(word.capitalize() for word in re.sub(r'\s+', ' ', name_part).strip().split())

    for pos in pos_cols:
        if pos in lineups_df.columns:
            lineups_df[f"{pos}_Name"] = lineups_df[pos].apply(extract_name)

    for _, r in research_df.iterrows():
        clean = r["Name"].lower()
        name_to_info[clean] = {
            "Projection": r["Proj"],
            "Ownership": r["Ownership"],
            "Salary": r["Salary"],
            "Value_per_k": r["Value_per_k"],
            "Display": r["Name"]
        }
        name_to_team[clean] = r["Team"]

    st.success(f"Research: **{len(research_df)}** players | Lineups: **{len(lineups_df)}** (Full X-Ray active)")
else:
    st.success(f"Research: **{len(research_df)}** players (Upload lineups for full X-Ray)")

# ====================== CLICKABLE LINK HELPERS ======================
team_url_map = {
    "ATL": "https://www.espn.com/nba/team/_/name/atl/atlanta-hawks",
    "BOS": "https://www.espn.com/nba/team/_/name/bos/boston-celtics",
    "BKN": "https://www.espn.com/nba/team/_/name/bkn/brooklyn-nets",
    "CHA": "https://www.espn.com/nba/team/_/name/cha/charlotte-hornets",
    "CHI": "https://www.espn.com/nba/team/_/name/chi/chicago-bulls",
    "CLE": "https://www.espn.com/nba/team/_/name/cle/cleveland-cavaliers",
    "DAL": "https://www.espn.com/nba/team/_/name/dal/dallas-mavericks",
    "DEN": "https://www.espn.com/nba/team/_/name/den/denver-nuggets",
    "DET": "https://www.espn.com/nba/team/_/name/det/detroit-pistons",
    "GS": "https://www.espn.com/nba/team/_/name/gs/golden-state-warriors",
    "HOU": "https://www.espn.com/nba/team/_/name/hou/houston-rockets",
    "IND": "https://www.espn.com/nba/team/_/name/ind/indiana-pacers",
    "LAC": "https://www.espn.com/nba/team/_/name/lac/la-clippers",
    "LAL": "https://www.espn.com/nba/team/_/name/lal/los-angeles-lakers",
    "MEM": "https://www.espn.com/nba/team/_/name/mem/memphis-grizzlies",
    "MIA": "https://www.espn.com/nba/team/_/name/mia/miami-heat",
    "MIL": "https://www.espn.com/nba/team/_/name/mil/milwaukee-bucks",
    "MIN": "https://www.espn.com/nba/team/_/name/min/minnesota-timberwolves",
    "NO": "https://www.espn.com/nba/team/_/name/no/new-orleans-pelicans",
    "NYK": "https://www.espn.com/nba/team/_/name/nyk/new-york-knicks",
    "OKC": "https://www.espn.com/nba/team/_/name/okc/oklahoma-city-thunder",
    "ORL": "https://www.espn.com/nba/team/_/name/orl/orlando-magic",
    "PHI": "https://www.espn.com/nba/team/_/name/phi/philadelphia-76ers",
    "PHO": "https://www.espn.com/nba/team/_/name/phx/phoenix-suns",
    "POR": "https://www.espn.com/nba/team/_/name/por/portland-trail-blazers",
    "SAC": "https://www.espn.com/nba/team/_/name/sac/sacramento-kings",
    "SA": "https://www.espn.com/nba/team/_/name/sa/san-antonio-spurs",
    "TOR": "https://www.espn.com/nba/team/_/name/tor/toronto-raptors",
    "UTA": "https://www.espn.com/nba/team/_/name/uta/utah-jazz",
    "WAS": "https://www.espn.com/nba/team/_/name/was/washington-wizards",
}

def clickable_name(name):
    url = f"https://www.espn.com/search/_/q/{urllib.parse.quote(name)}"
    return f'<a href="{url}" target="_blank">{name}</a>'

def clickable_team(team):
    url = team_url_map.get(team, "#")
    return f'<a href="{url}" target="_blank">{team}</a>'

# ====================== TABS ======================
tab_list = ["🔥 Hot Glance", "9K Studs", "🔀 Stacks", "⏱️ Minutes", "📈 Consistency", "⚡ Vegas & Pace"]
if lineups_df is not None:
    tab_list.append("📋 Lineup X-Ray")

tabs = st.tabs(tab_list)

# ====================== 1. HOT GLANCE ======================
with tabs[0]:
    st.subheader("🔥 Hot Glance")
    st.caption("Top 15 by Value/k • Stricter rules: Pure Value ≥ 5.75 | Multi-badge ≥ 5.25 + new edges")

    with st.expander("📌 Badge Legend – What each badge means & how it's calculated"):
        st.markdown("""
        - **🔥 High Value**: Value/k ≥ 5.0 (Proj ÷ (Salary/1000))  
        - **⏱️ Strong Min**: Projected minutes ≥ 30  
        - **📈 Hot Form**: 5-game FP > 90% of today's Proj  
        - **🎯 GPP Edge**: Proj > GPP Target (Proj Diff > 0)  

        **New edges**  
        - **🛡️ Dream Matchup**: Dvp ≤ -5.0%  
        - **⚡ Pace Booster**: Pace (+/-) ≥ +2.0  
        - **🛌 Fresh Legs**: Rest ≥ 3 days  
        - **💎 Elite DFSA**: DFSA Grade ≥ 70
        """)

    def get_badges(row):
        badges = []
        if row['Value_per_k'] >= 5.0: badges.append("🔥 High Value")
        if row.get("Minutes", 0) >= 30: badges.append("⏱️ Strong Min")
        if row.get("5gFP", 0) > row['Proj'] * 0.9: badges.append("📈 Hot Form")
        if row.get("Proj Diff", 0) > 0: badges.append("🎯 GPP Edge")
        if row.get("Dvp", 0) <= -5.0: badges.append("🛡️ Dream Matchup")
        if row.get("Pace (+/-)", 0) >= 2.0: badges.append("⚡ Pace Booster")
        if row.get("Rest", 0) >= 3: badges.append("🛌 Fresh Legs")
        if row.get("DFSA Grade", 0) >= 70: badges.append("💎 Elite DFSA")
        return badges

    research_df["badges"] = research_df.apply(get_badges, axis=1)
    research_df["badge_count"] = research_df["badges"].apply(len)

    mask = (
        (research_df["Value_per_k"] >= 5.75) |
        ((research_df["Value_per_k"] >= 5.25) & (research_df["badge_count"] > 1))
    )
    top = research_df[mask].nlargest(15, "Value_per_k")

    c = st.columns(5)
    for i, (_, p) in enumerate(top.iterrows()):
        with c[i % 5]:
            with st.container(border=True):
                st.markdown(f"**{clickable_name(p['Name'])}**", unsafe_allow_html=True)
                st.markdown(f"{clickable_team(p['Team'])} vs {p['Opp']}", unsafe_allow_html=True)
                st.metric("Proj", f"{p['Proj']:.1f}")
                st.metric("Value/k", f"{p['Value_per_k']:.2f}")
                st.metric("Own", f"{p['Ownership']:.1f}%")
                for b in p["badges"]:
                    st.markdown(f"<span style='color:#44FF88'>{b}</span>", unsafe_allow_html=True)

# ====================== 2. 9K STUDS ======================
with tabs[1]:
    st.subheader("9K Studs")
    st.caption("All players with Salary ≥ $9000 • Click player or team name for ESPN stats")

    with st.expander("📌 Badge Legend – What each badge means & how it's calculated"):
        st.markdown("""
        - **🔥 High Value**: Value/k ≥ 5.0 (Proj ÷ (Salary/1000))  
        - **⏱️ Strong Min**: Projected minutes ≥ 32  
        - **📈 Hot Form**: 5-game FP > 90% of today's Proj  
        - **🎯 GPP Edge**: Proj > GPP Target (Proj Diff > 0)  

        **New edges**  
        - **🛡️ Dream Matchup**: Dvp ≤ -5.0%  
        - **⚡ Pace Booster**: Pace (+/-) ≥ +2.0  
        - **🛌 Fresh Legs**: Rest ≥ 3 days  
        - **💎 Elite DFSA**: DFSA Grade ≥ 70
        """)

    studs = research_df[research_df["Salary"] >= 9000].copy()

    sort_options = {
        "Projection (high to low)": "Proj",
        "Value/k": "Value_per_k",
        "Ceiling": "Ceiling",
        "Ownership %": "Ownership",
        "USG%": "USG%",
    }
    sort_by = st.selectbox("Sort cards by", options=list(sort_options.keys()), index=0)
    studs = studs.sort_values(sort_options[sort_by], ascending=False)

    cols = st.columns(3)
    for i, (_, p) in enumerate(studs.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{clickable_name(p['Name'])}**", unsafe_allow_html=True)
                st.markdown(f"{clickable_team(p['Team'])} vs {p['Opp']}", unsafe_allow_html=True)
                st.metric("Proj", f"{p['Proj']:.1f}")
                st.metric("Value/k", f"{p['Value_per_k']:.2f}")
                st.metric("Own", f"{p['Ownership']:.1f}%")
                st.caption(f"Dvp: {p.get('Dvp', 0):.1f}%")

                badges = []
                if p['Value_per_k'] >= 5.0: badges.append("🔥 High Value")
                if p.get("Minutes", 0) >= 32: badges.append("⏱️ Strong Min")
                if p.get("5gFP", 0) > p['Proj'] * 0.9: badges.append("📈 Hot Form")
                if p.get("Proj Diff", 0) > 0: badges.append("🎯 GPP Edge")
                if p.get("Dvp", 0) <= -5.0: badges.append("🛡️ Dream Matchup")
                if p.get("Pace (+/-)", 0) >= 2.0: badges.append("⚡ Pace Booster")
                if p.get("Rest", 0) >= 3: badges.append("🛌 Fresh Legs")
                if p.get("DFSA Grade", 0) >= 70: badges.append("💎 Elite DFSA")

                for b in badges:
                    st.markdown(f"<span style='color:#44FF88'>{b}</span>", unsafe_allow_html=True)

# ====================== 3. STACKS ======================
with tabs[2]:
    st.subheader("🔀 Recommended Core Stacks")
    st.caption("**Smart logic**:\n1. Most players in top 10 ownership\n2. Tie → highest game total\n3. Head-to-head → favorite")

    top_owned = research_df.nlargest(10, "Ownership")
    team_stats = top_owned.groupby("Team").agg(
        Player_Count=("Name", "count"),
        Game_Total=("Total O/U", "first"),
        Team_Total=("Team Total", "first"),
        Opp=("Opp", "first")
    ).reset_index()

    team_stats = team_stats.sort_values(
        by=["Player_Count", "Game_Total", "Team_Total"],
        ascending=[False, False, False]
    )

    for _, row in team_stats.head(4).iterrows():
        team = row["Team"]
        count = int(row["Player_Count"])
        players = top_owned[top_owned["Team"] == team]["Name"].tolist()

        if _ == 0:
            st.markdown(f"**#1 Recommended 3-Stack → {clickable_team(team)}** ({count} players in top 10 owned)", unsafe_allow_html=True)
        else:
            st.markdown(f"**{clickable_team(team)}** — {count} players in top 10 ownership", unsafe_allow_html=True)

        clickable_players = [clickable_name(p) for p in players[:8]]
        st.write(" → " + ", ".join(clickable_players), unsafe_allow_html=True)
        st.write("---")

# ====================== 4. MINUTES ======================
with tabs[3]:
    st.subheader("⏱️ Minutes & Usage")
    st.caption("**Points per Minute** = scoring efficiency when on the floor.\n**Min_Trend** = Projected minutes - 5-game average.")
    st.dataframe(research_df.nlargest(12, "Points_per_min")[["Name", "Team", "Minutes", "Points_per_min", "Proj", "Ownership"]], width="stretch")
    st.dataframe(research_df.nlargest(12, "Minutes")[["Name", "Team", "Minutes", "5gMin", "Min_Trend"]], width="stretch")

# ====================== 5. CONSISTENCY ======================
with tabs[4]:
    st.subheader("📈 Consistency & Recent Form + GPP")
    fig = px.scatter(research_df, x="5gFP", y="Proj", color="Ownership", size="Value_per_k", hover_name="Name")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(research_df.nlargest(12, "5gFP")[["Name", "Team", "Proj", "Value_per_k", "Ownership", "5gFP"]], width="stretch")

    st.subheader("GPP Insights")
    gpp = research_df.nlargest(12, "Proj Diff")[["Name", "Team", "Proj", "GPP Target", "7x%", "Proj Diff", "Ownership"]]
    st.dataframe(gpp, width="stretch")

# ====================== 6. VEGAS & PACE ======================
with tabs[5]:
    st.subheader("⚡ Vegas & Pace Highlights")
    games = research_df[['Team', 'Opp', 'Total O/U']].drop_duplicates().sort_values('Total O/U', ascending=False)
    st.dataframe(games.head(6), width="stretch")
    pace_teams = research_df[['Team', 'Pace Team']].drop_duplicates().sort_values('Pace Team', ascending=False).head(8)
    st.dataframe(pace_teams, width="stretch")

# ====================== 7. LINEUP X-RAY ======================
if lineups_df is not None:
    with tabs[6]:
        st.subheader("📋 Lineup X-Ray")
        exposures = [name for pos in pos_cols for name in lineups_df.get(f"{pos}_Name", pd.Series()).dropna()]
        exp_df = pd.Series(exposures).value_counts().reset_index()
        exp_df.columns = ["Player", "Count"]
        total = len(lineups_df)
        exp_df["Exposure %"] = (exp_df["Count"] / total * 100).round(1)
        exp_df = exp_df.sort_values("Count", ascending=False).head(20)
        st.subheader("Exposures")
        st.dataframe(exp_df, width="stretch")

st.caption("DFS X-Ray Full v2.1 — Clickable player & team links fixed everywhere")