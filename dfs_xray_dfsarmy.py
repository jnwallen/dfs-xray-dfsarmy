import streamlit as st
import pandas as pd
from collections import Counter
import plotly.express as px
import re
from io import StringIO

st.set_page_config(page_title="DFS X-Ray — NBA Legend Edition", layout="wide")

col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image("blceggLogo.png", width=180)
    except:
        pass
with col_title:
    st.title("DFS X-Ray — NBA Legend Edition")
    st.markdown("**Built For B Clegg.  Because the Browns Aren't the Only Winners**")

st.markdown("**Color Key:** Red = #1 most exposed • Blue = #2 • Pink = #3 • Green = #4 • Orange = #5")

col1, col2 = st.columns(2)
with col1:
    players_file = st.file_uploader("1. Research Station CSV", type="csv")
with col2:
    lineups_file = st.file_uploader("2. Lineups CSV", type="csv")

if not players_file or not lineups_file:
    st.stop()

@st.cache_data
def parse_dfsarmy(players_bytes, lineups_bytes):
    # Projections (double header)
    proj = pd.read_csv(players_bytes, header=1)
    name_to_info = {}
    name_to_team = {}
    for _, r in proj.iterrows():
        raw_name = str(r.get("Name", "")).strip()
        if raw_name:
            clean_name = re.sub(r'\s+', ' ', raw_name).strip().lower()
            display_name = ' '.join(word.capitalize() for word in clean_name.split())
            
            salary_str = str(r.get("Salary", "0")).replace('$', '').replace(',', '').strip()
            salary = float(salary_str) if salary_str else 0
            ownership_str = str(r.get("Ownership", "0")).replace('%', '').strip()
            ownership = float(ownership_str) if ownership_str else 0

            name_to_info[clean_name] = {
                "Projection": float(r.get("Proj", 0)),
                "Ownership": ownership,
                "Salary": salary,
                "Value": round(float(r.get("Proj", 0)) / (salary / 1000), 2) if salary > 0 else 0,
                "Display": display_name
            }
            team = str(r.get("Team", "")).strip().upper()
            if team:
                name_to_team[clean_name] = team

    # Lineups
    lines = []
    with lineups_bytes as f:
        for line in f:
            line_str = line.decode('utf-8').strip()
            if not line_str: continue
            if "Position" in line_str or "Name + ID" in line_str or line_str.count(',') > 15:
                break
            lines.append(line_str)

    clean_csv = "\n".join(lines)
    lineups_part = pd.read_csv(StringIO(clean_csv))

    pos_cols = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']

    def extract_name(cell):
        if pd.isna(cell): return None
        cell = str(cell).strip()
        if '(' in cell:
            name_part = cell.split('(')[0].strip()
        else:
            name_part = cell
        return ' '.join(word.capitalize() for word in re.sub(r'\s+', ' ', name_part).strip().split())

    for pos in pos_cols:
        if pos in lineups_part.columns:
            lineups_part[f"{pos}_Name"] = lineups_part[pos].apply(extract_name)

    # Exposures
    exposures = [name for pos in pos_cols for name in lineups_part.get(f"{pos}_Name", pd.Series()).dropna()]
    exp_df = pd.Series(exposures).value_counts().reset_index()
    exp_df.columns = ["Player", "Count"]
    total = len(lineups_part)
    exp_df["Exposure %"] = (exp_df["Count"] / total * 100).round(1)
    exp_df = exp_df.sort_values("Count", ascending=False).reset_index(drop=True)
    exp_df["Rank"] = exp_df.index + 1
    color_map = {1:"#FF4444", 2:"#4488FF", 3:"#FF44AA", 4:"#44FF88", 5:"#FFAA44"}
    exp_df["Color"] = exp_df["Rank"].map(lambda r: color_map.get(r, "#AAAAAA"))
    player_color = dict(zip(exp_df["Player"], exp_df["Color"]))

    return lineups_part, name_to_info, name_to_team, exp_df, player_color, pos_cols, total

lineups_df, name_to_info, name_to_team, exposure_df, player_color, pos_cols, total_lineups = parse_dfsarmy(players_file, lineups_file)

st.success(f"Loaded **{total_lineups}** lineups successfully!")

# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 All Lineups", "🃏 Lineup Cards", "🔍 Player Drill-Down", "📊 Exposures", "⚠️ Traps", "🔀 Stacks"])

with tab1:
    st.subheader(f"All Lineups ({total_lineups})")
    disp = pd.DataFrame()
    for pos in pos_cols:
        if f"{pos}_Name" in lineups_df.columns:
            disp[pos] = lineups_df[f"{pos}_Name"]
    st.dataframe(disp, width="stretch", height=700)

with tab2:
    st.subheader("🃏 Lineup Cards")
    if len(lineups_df) > 0:
        lineup_num = st.selectbox("Select Lineup", range(len(lineups_df)))
        row = lineups_df.iloc[lineup_num]
        
        # Build stack label like SaberSim (e.g. "DAL 3 • SAS 2 • LAL 1")
        teams = []
        for pos in pos_cols:
            name_col = f"{pos}_Name"
            if name_col in row and pd.notna(row[name_col]):
                clean_name = row[name_col].lower()
                team = name_to_team.get(clean_name, "UNK")
                if team != "UNK":
                    teams.append(team)
        stack_counter = Counter(teams)
        stack_parts = [f"{team} {count}" for team, count in sorted(stack_counter.items(), key=lambda x: -x[1])]
        stack_label = " • ".join(stack_parts) if stack_parts else "No Team Data"

        with st.container(border=True):
            st.markdown(f"**Stack:** {stack_label}")
            c = st.columns([1,4,1.5,1.5,1.5,1.2])
            c[0].markdown("**Pos**")
            c[1].markdown("**Player**")
            c[2].markdown("**Proj**")
            c[3].markdown("**Value**")
            c[4].markdown("**Own**")
            for pos in pos_cols:
                name_col = f"{pos}_Name"
                if name_col in row and pd.notna(row[name_col]):
                    name = row[name_col]
                    clean_lower = name.lower()
                    info = name_to_info.get(clean_lower, {})
                    color = player_color.get(name, "#FFFFFF")
                    c[0].markdown(f"**{pos}**")
                    c[1].markdown(f"<span style='color:{color}'>**{name}**</span>", unsafe_allow_html=True)
                    c[2].write(f"{info.get('Projection',0):.1f}")
                    c[3].write(f"{info.get('Value',0):.2f}")
                    c[4].write(f"{info.get('Ownership',0):.1f}%")

with tab3:
    st.subheader("🔍 Player Drill-Down")
    search_player = st.text_input("Search player name")
    if search_player:
        search_lower = search_player.lower()
        matching = [n for n in name_to_info.keys() if search_lower in n]
        if matching:
            clean_name = matching[0]
            display_name = name_to_info[clean_name]["Display"]
            info = name_to_info[clean_name]
            exp_row = exposure_df[exposure_df["Player"] == display_name]
            exp_pct = exp_row["Exposure %"].iloc[0] if not exp_row.empty else 0
            gap = round(exp_pct - info.get("Ownership", 0), 1)

            st.success(f"**{display_name}** — In **{int(exp_row['Count'].iloc[0] if not exp_row.empty else 0)}** lineups ({exp_pct:.1f}%) | Gap: **{gap:+.1f}%**")

            # Teammates
            st.subheader("Most Common Teammates")
            mask = pd.Series(False, index=lineups_df.index)
            for pos in pos_cols:
                col = f"{pos}_Name"
                if col in lineups_df.columns:
                    mask |= (lineups_df[col] == display_name)
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
                fig = px.bar(tm_df, x="Teammate", y="Count", title="Most Common Teammates", color_discrete_map=player_color)
                st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("📊 Exposures")
    exp_display = exposure_df.head(30).copy()
    exp_display["Ownership %"] = exp_display["Player"].map(lambda x: name_to_info.get(x.lower(), {}).get("Ownership", 0))
    exp_display["Leverage Gap %"] = (exp_display["Exposure %"] - exp_display["Ownership %"]).round(1)
    exp_display["Value"] = exp_display["Player"].map(lambda x: name_to_info.get(x.lower(), {}).get("Value", 0))
    if "Color" in exp_display.columns:
        exp_display = exp_display.drop(columns=["Color"])
    st.dataframe(exp_display, width="stretch")

with tab5:
    st.subheader("⚠️ Traps")
    traps = []
    for clean_name, info in name_to_info.items():
        display_name = info["Display"]
        exp_row = exposure_df[exposure_df["Player"] == display_name]
        exp_pct = exp_row["Exposure %"].iloc[0] if not exp_row.empty else 0
        gap = exp_pct - info.get("Ownership", 0)
        value = info.get("Value", 0)
        if exp_pct > 20 and (value < 4.8 or gap > 10):
            traps.append({"Player": display_name, "Value": round(value,2), "Gap %": round(gap,1), "Exposure %": round(exp_pct,1)})
    if traps:
        st.dataframe(pd.DataFrame(traps).sort_values("Gap %", ascending=False), width="stretch")
    else:
        st.success("No major traps detected")

with tab6:
    st.subheader("🔀 Stacks Analysis")
    if len(lineups_df) > 0 and name_to_team:
        stack_labels = []
        for idx, row in lineups_df.iterrows():
            teams = []
            for pos in pos_cols:
                name_col = f"{pos}_Name"
                if name_col in row and pd.notna(row[name_col]):
                    clean = row[name_col].lower()
                    team = name_to_team.get(clean, "UNK")
                    if team != "UNK":
                        teams.append(team)
            if teams:
                counter = Counter(teams)
                parts = [f"{team} {cnt}" for team, cnt in sorted(counter.items(), key=lambda x: -x[1])]
                stack_labels.append(" • ".join(parts))
        
        stack_series = pd.Series(stack_labels)
        top_stacks = stack_series.value_counts().head(15)
        
        st.write("**Most Common Stack Patterns**")
        st.bar_chart(top_stacks)

        st.write("**Number of Teams per Lineup**")
        num_teams = stack_series.str.count("•") + 1
        fig = px.histogram(num_teams, nbins=8, title="Stack Size Distribution")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(top_stacks.reset_index().head(10), width="stretch")

    else:
        st.info("No team data available for stack analysis.")

st.caption("DFS Army v2.13 — Fixed histogram error + clean stack display")