import streamlit as st
import pandas as pd
from collections import Counter
import plotly.express as px

st.set_page_config(page_title="DFS X-Ray — NBA Legend", layout="wide")

# ====================== HEADER ======================
col_logo, col_title = st.columns([1, 3])
with col_logo:
    st.image("blceggLogo.png", width=220)

with col_title:
    st.markdown("# DFS X-Ray — NBA Legend Edition")
    st.markdown("**Built for bclegg_22 — same tools as the SaberSim version**")

st.markdown("---")

# ====================== UPLOADERS ======================
col1, col2 = st.columns(2)
with col1:
    players_file = st.file_uploader("1. Players CSV", type="csv")
with col2:
    lineups_file = st.file_uploader("2. Lineups CSV", type="csv")

if not players_file or not lineups_file:
    st.stop()

# (Rest of the code is the same as before - loading, drill-down, exposures, traps)

# Players
players = pd.read_csv(players_file)
players = players.rename(columns={"Points": "Projection", "ProjOwn": "Ownership"})

name_to_info = {}
for _, r in players.iterrows():
    name = str(r["Name"]).strip()
    name_to_info[name] = {
        "Projection": float(r.get("Projection", 0)),
        "Ownership": float(r.get("Ownership", 0))
    }

# Lineups
df = pd.read_csv(lineups_file, usecols=range(12))
df = df[df.iloc[:, 0].notna()].copy().reset_index(drop=True)

pos_cols = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']

for pos in pos_cols:
    if pos in df.columns:
        df[f"{pos}_Name"] = df[pos].astype(str).str.split('(').str[0].str.strip()

player_map = {}
for name, info in name_to_info.items():
    proj = info["Projection"]
    player_map[name] = {
        "Salary": 0,
        "Projection": proj,
        "Ownership": info["Ownership"],
        "Value": round(proj / 5, 2) if proj > 0 else 0
    }

# Exposures
exposures = []
for pos in pos_cols:
    col = f"{pos}_Name"
    if col in df.columns:
        for name in df[col].dropna():
            clean = str(name).strip()
            if clean and clean.lower() != 'nan':
                exposures.append(clean)

exp_df = pd.Series(exposures).value_counts().reset_index()
exp_df.columns = ["Player", "Count"]
total = len(df)
exp_df["Exposure %"] = (exp_df["Count"] / total * 100).round(1)
exp_df = exp_df.sort_values("Count", ascending=False).reset_index(drop=True)
exp_df["Rank"] = exp_df.index + 1

color_map = {1:"#FF4444", 2:"#4488FF", 3:"#FF44AA", 4:"#44FF88", 5:"#FFAA44"}
exp_df["Color"] = exp_df["Rank"].map(lambda r: color_map.get(r, "#AAAAAA"))
player_color = dict(zip(exp_df["Player"], exp_df["Color"]))

st.success(f"Loaded **{total}** lineups!")

st.markdown("**Color Key:** Red = #1 most exposed • Blue = #2 • Pink = #3 • Green = #4 • Orange = #5")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["All Lineups", "Lineup Cards", "🔍 Player Drill-Down", "Exposures", "Traps"])

with tab1:
    st.subheader(f"All Lineups ({total})")
    disp = df[['Entry ID', 'Contest Name']].copy() if 'Entry ID' in df.columns else pd.DataFrame()
    for pos in pos_cols:
        if f"{pos}_Name" in df.columns:
            disp[pos] = df[f"{pos}_Name"]
    st.dataframe(disp, use_container_width=True, height=700)

with tab2:
    st.subheader("🃏 Lineup Cards")
    if len(df) > 0:
        lineup_num = st.selectbox("Select Lineup", range(len(df)), format_func=lambda x: f"Lineup {x+1}")
        row = df.iloc[lineup_num]
        c = st.columns([1,4,1.5,1.5,1.2])
        c[0].markdown("**Pos**")
        c[1].markdown("**Player**")
        c[2].markdown("**Proj**")
        c[3].markdown("**Value** (approx)")
        c[4].markdown("**Own**")
        for pos in pos_cols:
            name_col = f"{pos}_Name"
            if name_col in row and pd.notna(row[name_col]):
                name = str(row[name_col]).strip()
                info = player_map.get(name, {})
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
        matching = [n for n in player_map.keys() if search_player.lower() in n.lower()]
        if matching:
            name = matching[0]
            info = player_map[name]
            exp_row = exp_df[exp_df["Player"] == name]
            exp_pct = exp_row["Exposure %"].iloc[0] if not exp_row.empty else 0
            gap = round(exp_pct - info.get("Ownership", 0), 1)
            
            st.success(f"**{name}** — Approx Value: **{info.get('Value',0):.2f}** | Leverage Gap: **{gap:+.1f}%**")
            
            mask = pd.Series(False, index=df.index)
            for pos in pos_cols:
                col = f"{pos}_Name"
                if col in df.columns:
                    mask |= (df[col] == name)
            containing = df[mask]
            
            co = []
            for _, r in containing.iterrows():
                for pos in pos_cols:
                    col = f"{pos}_Name"
                    if col in r and pd.notna(r[col]) and str(r[col]).strip() != name:
                        co.append(str(r[col]).strip())
            
            co_df = pd.Series(Counter(co)).sort_values(ascending=False).head(10).reset_index()
            co_df.columns = ["Teammate", "Times Together"]
            
            fig = px.bar(co_df, y="Teammate", x="Times Together", orientation='h', title="Most Common Teammates")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(co_df, use_container_width=True)
        else:
            st.warning("Player not found")

with tab4:
    st.subheader("📊 Exposures + Leverage")
    exp_display = exp_df.head(30).copy()
    exp_display["Ownership %"] = exp_display["Player"].map(lambda x: player_map.get(x, {}).get("Ownership", 0))
    exp_display["Leverage Gap %"] = (exp_display["Exposure %"] - exp_display["Ownership %"]).round(1)
    exp_display["Value (approx)"] = exp_display["Player"].map(lambda x: player_map.get(x, {}).get("Value", 0))
    st.dataframe(exp_display, use_container_width=True)

with tab5:
    st.subheader("⚠️ Traps")
    traps = []
    for name, info in player_map.items():
        exp_row = exp_df[exp_df["Player"] == name]
        exp_pct = exp_row["Exposure %"].iloc[0] if not exp_row.empty else 0
        gap = exp_pct - info.get("Ownership", 0)
        value = info.get("Value", 0)
        if exp_pct > 20 and (value < 4.8 or gap > 10):
            traps.append({"Player": name, "Value": round(value,2), "Gap %": round(gap,1), "Exposure %": round(exp_pct,1)})
    if traps:
        st.dataframe(pd.DataFrame(traps).sort_values("Gap %", ascending=False), use_container_width=True)
    else:
        st.success("No major traps detected")

st.caption("NBA Legend Edition — Full Drill-Down + Leverage Gap")