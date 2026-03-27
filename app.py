import streamlit as st
import pandas as pd
from collections import Counter
import plotly.express as px
import re
from io import StringIO

st.set_page_config(page_title="DFS X-Ray Full", layout="wide")

# ====================== HEADER WITH BOTH LOGOS ======================
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
        if pd.isna(val): return 0.0
        s = str(val).replace('$', '').replace(',', '').replace('%', '').strip()
        try: return float(s)
        except: return 0.0

    df["Salary"] = df["Salary"].apply(clean_num)
    df["Ownership"] = df["Ownership"].apply(clean_num)
    df["Proj"] = df["Proj"].apply(clean_num)
    df["Value"] = df["Value"].apply(clean_num)
    df["GPP Target"] = df.get("GPP Target", pd.Series([0]*len(df))).apply(clean_num)
    df["7x%"] = df.get("7x%", pd.Series([0]*len(df))).apply(clean_num)
    df["Proj Diff"] = df.get("Proj Diff", pd.Series([0]*len(df))).apply(clean_num)

    df["Team"] = df["Team"].astype(str).str.upper().str.strip()
    df["Value_per_k"] = (df["Proj"] / (df["Salary"] / 1000)).round(2)
    df["Points_per_min"] = (df["Proj"] / df["Minutes"]).round(2) if "Minutes" in df.columns and df["Minutes"].max() > 0 else 0.0
    df["Min_Trend"] = df.get("Minutes", 0) - df.get("5gMin", 0)

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

# ====================== TABS ======================
tab_list = ["🔥 Hot Glance", "📊 Value Plays", "📈 Consistency", "⏱️ Minutes", "🔀 Stacks", "⚡ Vegas & Pace"]
if lineups_df is not None:
    tab_list.append("📋 Lineup X-Ray")

tabs = st.tabs(tab_list)

# Research Tabs (0-5)
with tabs[0]:
    st.subheader("🔥 Hot Glance")
    top = research_df.nlargest(10, "Value_per_k")
    c = st.columns(5)
    for i, (_, p) in enumerate(top.iterrows()):
        with c[i % 5]:
            with st.container(border=True):
                st.markdown(f"**{p['Name']}**")
                st.caption(f"{p['Team']}")
                st.metric("Proj", f"{p['Proj']:.1f}")
                st.metric("Value/k", f"{p['Value_per_k']:.2f}")
                st.metric("Own", f"{p['Ownership']:.1f}%")
                badges = []
                if p['Value_per_k'] >= 5.0: badges.append("🔥 High Value")
                if p.get("Minutes", 0) >= 30: badges.append("⏱️ Strong Min")
                if p.get("5gFP", 0) > p['Proj'] * 0.9: badges.append("📈 Hot Form")
                if p.get("Proj Diff", 0) > 0: badges.append("🎯 GPP Edge")
                for b in badges:
                    st.markdown(f"<span style='color:#44FF88'>{b}</span>", unsafe_allow_html=True)

with tabs[1]:
    st.subheader("Value Plays")
    chalk = research_df[research_df["Ownership"] >= 20].nlargest(12, "Value_per_k")
    st.write("**Chalk Value**")
    st.dataframe(chalk[["Name", "Team", "Proj", "Value_per_k", "Ownership", "Salary"]], width="stretch")
    sneaky = research_df[research_df["Ownership"] < 20].nlargest(12, "Value_per_k")
    st.write("**Sneaky Value**")
    st.dataframe(sneaky[["Name", "Team", "Proj", "Value_per_k", "Ownership", "Salary"]], width="stretch")

with tabs[2]:
    st.subheader("Consistency & Recent Form + GPP")
    fig = px.scatter(research_df, x="5gFP", y="Proj", color="Ownership", size="Value_per_k", hover_name="Name")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(research_df.nlargest(12, "5gFP")[["Name", "Team", "Proj", "Value_per_k", "Ownership", "5gFP"]], width="stretch")
    st.subheader("GPP Insights")
    st.dataframe(research_df.nlargest(12, "Proj Diff")[["Name", "Team", "Proj", "GPP Target", "7x%", "Proj Diff", "Ownership"]], width="stretch")

with tabs[3]:
    st.subheader("⏱️ Minutes & Usage")
    st.dataframe(research_df.nlargest(12, "Points_per_min")[["Name", "Team", "Minutes", "Points_per_min", "Proj"]], width="stretch")
    st.dataframe(research_df.nlargest(12, "Minutes")[["Name", "Team", "Minutes", "5gMin", "Min_Trend"]], width="stretch")

with tabs[4]:
    st.subheader("Recommended Core Stacks")
    top_owned = research_df.nlargest(10, "Ownership")
    team_counts = top_owned["Team"].value_counts().head(4)
    for team, count in team_counts.items():
        players = top_owned[top_owned["Team"] == team]["Name"].tolist()
        st.write(f"**{team}** — {count} players in top 10 ownership")
        st.write(" → " + ", ".join(players[:8]))

with tabs[5]:
    st.subheader("⚡ Vegas & Pace Highlights")
    games = research_df[['Team', 'Opp', 'Total O/U']].drop_duplicates().sort_values('Total O/U', ascending=False)
    st.dataframe(games.head(6), width="stretch")
    pace_teams = research_df[['Team', 'Pace Team']].drop_duplicates().sort_values('Pace Team', ascending=False).head(8)
    st.dataframe(pace_teams, width="stretch")

# ====================== FULL X-RAY TAB ======================
if lineups_df is not None:
    with tabs[6]:
        st.subheader("📋 Lineup X-Ray")

        # Exposures
        exposures = [name for pos in pos_cols for name in lineups_df.get(f"{pos}_Name", pd.Series()).dropna()]
        exp_df = pd.Series(exposures).value_counts().reset_index()
        exp_df.columns = ["Player", "Count"]
        total = len(lineups_df)
        exp_df["Exposure %"] = (exp_df["Count"] / total * 100).round(1)
        exp_df = exp_df.sort_values("Count", ascending=False).head(20)
        st.subheader("Exposures")
        st.dataframe(exp_df, width="stretch")

        # Lineup Cards (fixed layout)
        st.subheader("Lineup Cards")
        lineup_num = st.selectbox("Select Lineup", range(len(lineups_df)))
        row = lineups_df.iloc[lineup_num]

        teams = []
        for pos in pos_cols:
            name_col = f"{pos}_Name"
            if name_col in row and pd.notna(row[name_col]):
                clean = row[name_col].lower()
                team = name_to_team.get(clean, "UNK")
                if team != "UNK":
                    teams.append(team)
        stack_counter = Counter(teams)
        stack_label = " • ".join([f"{team} {cnt}" for team, cnt in sorted(stack_counter.items(), key=lambda x: -x[1])])
        st.markdown(f"**Stack:** {stack_label}")

        c = st.columns([1, 4, 1.5, 1.5, 1.5, 1.2])
        c[0].markdown("**Pos**")
        c[1].markdown("**Player**")
        c[2].markdown("**Proj**")
        c[3].markdown("**Value**")
        c[4].markdown("**Own**")
        for pos in pos_cols:
            name_col = f"{pos}_Name"
            if name_col in row and pd.notna(row[name_col]):
                name = row[name_col]
                clean = name.lower()
                info = name_to_info.get(clean, {})
                c[0].markdown(f"**{pos}**")
                c[1].markdown(f"**{name}**")
                c[2].write(f"{info.get('Projection',0):.1f}")
                c[3].write(f"{info.get('Value_per_k',0):.2f}")
                c[4].write(f"{info.get('Ownership',0):.1f}%")

        # Player Drill-Down with Teammates
        st.subheader("Player Drill-Down")
        search_player = st.text_input("Search player name")
        if search_player:
            search_lower = search_player.lower()
            matching = [n for n in name_to_info.keys() if search_lower in n]
            if matching:
                clean_name = matching[0]
                display_name = name_to_info[clean_name]["Display"]
                info = name_to_info[clean_name]

                # Count lineups player is in
                mask = pd.Series(False, index=lineups_df.index)
                for pos in pos_cols:
                    col = f"{pos}_Name"
                    if col in lineups_df.columns:
                        mask |= (lineups_df[col] == display_name)
                lineup_count = mask.sum()

                st.success(f"**{display_name}** — In **{lineup_count}** lineups | Proj {info['Projection']:.1f} | Value/k {info['Value_per_k']:.2f} | Own {info['Ownership']:.1f}%")

                # Most common teammates
                st.subheader("Most Common Teammates")
                teammate_lineups = lineups_df[mask]
                teammates = []
                for pos in pos_cols:
                    col = f"{pos}_Name"
                    if col in teammate_lineups.columns:
                        for tm in teammate_lineups[col].dropna():
                            if tm != display_name:
                                teammates.append(tm)
                if teammates:
                    tm_df = pd.Series(teammates).value_counts().head(10).reset_index()
                    tm_df.columns = ["Teammate", "Count"]
                    fig = px.bar(tm_df, x="Teammate", y="Count", title="Most Common Teammates")
                    st.plotly_chart(fig, use_container_width=True)

        # Traps
        st.subheader("Traps")
        traps = []
        for clean_name, info in name_to_info.items():
            exp_row = exp_df[exp_df["Player"] == info["Display"]]
            exp_pct = exp_row["Exposure %"].iloc[0] if not exp_row.empty else 0
            gap = exp_pct - info.get("Ownership", 0)
            if exp_pct > 20 and (info.get("Value_per_k", 0) < 4.8 or gap > 10):
                traps.append({"Player": info["Display"], "Value/k": info.get("Value_per_k", 0), "Gap %": round(gap,1), "Exposure %": round(exp_pct,1)})
        if traps:
            st.dataframe(pd.DataFrame(traps).sort_values("Gap %", ascending=False), width="stretch")
        else:
            st.success("No major traps detected")

        # Stack Analysis
        st.subheader("Stack Analysis")
        if len(lineups_df) > 0:
            stack_labels = []
            for _, row in lineups_df.iterrows():
                teams = [name_to_team.get(row[f"{pos}_Name"].lower(), "UNK") for pos in pos_cols if f"{pos}_Name" in row and pd.notna(row[f"{pos}_Name"])]
                counter = Counter([t for t in teams if t != "UNK"])
                parts = [f"{team} {cnt}" for team, cnt in sorted(counter.items(), key=lambda x: -x[1])]
                stack_labels.append(" • ".join(parts))
            stack_series = pd.Series(stack_labels)
            st.bar_chart(stack_series.value_counts().head(15))

st.caption("DFS X-Ray Full v1.1 — Complete with teammate drill-down")