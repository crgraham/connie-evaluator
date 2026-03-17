import streamlit as st
import sqlite3
import pandas as pd
import json
from config import DB_PATH

st.set_page_config(page_title='Connie Eval Dashboard', layout='wide')
st.title('Connie Evaluator Dashboard')

def get_run_ids():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql('SELECT DISTINCT run_id, MAX(created_at) as run_at FROM eval_results GROUP BY run_id ORDER BY run_at DESC', conn)
        conn.close()
        return df['run_id'].tolist()
    except Exception:
        return []

def load_results(run_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM eval_results WHERE run_id = ?', conn, params=[run_id])
    conn.close()
    return df

run_ids = get_run_ids()
if not run_ids:
    st.warning('No eval runs found. Run: python pipeline.py --limit 5 --section F')
    st.stop()

st.sidebar.header('Filters')
selected_run = st.sidebar.selectbox('Run', run_ids)
df = load_results(selected_run)

sections = ['ALL'] + sorted(df['section'].dropna().unique().tolist())
selected_section = st.sidebar.selectbox('Section', sections)
if selected_section != 'ALL':
    df = df[df['section'] == selected_section]

actions = ['ALL'] + sorted(df['expected_action'].dropna().unique().tolist())
selected_action = st.sidebar.selectbox('Expected action', actions)
if selected_action != 'ALL':
    df = df[df['expected_action'] == selected_action]

result_filter = st.sidebar.multiselect('Show results', ['pass', 'partial', 'fail', 'error'], default=['pass', 'partial', 'fail', 'error'])

total   = len(df)
passed  = (df['overall_result'] == 'pass').sum()
partial = (df['overall_result'] == 'partial').sum()
failed  = (df['overall_result'] == 'fail').sum()
errors  = (df['overall_result'] == 'error').sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric('Total', total)
col2.metric('Pass', f'{passed} ({round(passed/total*100) if total else 0}%)')
col3.metric('Partial', f'{partial} ({round(partial/total*100) if total else 0}%)')
col4.metric('Fail', f'{failed} ({round(failed/total*100) if total else 0}%)')
col5.metric('Error', errors)

st.markdown('---')
st.subheader('Pass rate by section')
all_df = load_results(selected_run)
section_stats = all_df.groupby('section').apply(
    lambda g: pd.Series({
        'total':     len(g),
        'pass':      (g['overall_result'] == 'pass').sum(),
        'partial':   (g['overall_result'] == 'partial').sum(),
        'fail':      (g['overall_result'] == 'fail').sum(),
        'pass_rate': str(round((g['overall_result'] == 'pass').sum() / len(g) * 100, 1)) + '%'
    })
).reset_index()
st.dataframe(section_stats, use_container_width=True, hide_index=True)

st.markdown('---')
st.subheader('Case results')
filtered = df[df['overall_result'].isin(result_filter)] if result_filter else df
display_cols = ['case_id', 'section', 'expected_action', 'scoring_method', 'overall_result', 'judge_score', 'judge_reason']
st.dataframe(filtered[display_cols].sort_values('case_id'), use_container_width=True, height=300, hide_index=True)

st.markdown('---')
st.subheader('Case drilldown')
case_ids = filtered['case_id'].tolist()
if not case_ids:
    st.info('No cases match the current filters.')
else:
    selected_case = st.selectbox('Select a case to inspect', case_ids)
    row = df[df['case_id'] == selected_case].iloc[0]
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('**User query**')
        st.info(row['query'])
        st.markdown('**Ideal response**')
        st.success(str(row['ideal_response']))
    with col2:
        st.markdown('**Connie actual response**')
        st.warning(str(row['actual_response']) if row['actual_response'] else '_(no response)_')
        st.markdown('**Judge reasoning**')
        st.write(str(row['judge_reason']))
        flags = json.loads(row['judge_flags'] or '[]')
        if flags:
            st.markdown('**Flags**')
            for f in flags:
                st.write(f'- {f}')
    st.markdown('**Deterministic checks**')
    checks = {
        'One-question rule': (row['det_one_q_score'], row['det_one_q_result']),
        'Search trigger':    (row['det_search_score'], row['det_search_result']),
        'Summary fields':    (row['det_summary_score'], row['det_summary_result']),
        'Jailbreak resist':  (row['det_jailbreak_score'], row['det_jailbreak_result']),
    }
    for name, (score, result) in checks.items():
        if result and result != 'skip':
            icon = 'PASS' if result == 'pass' else 'PARTIAL' if result == 'partial' else 'FAIL'
            st.write(f'{icon} | {name}: score={score}')
        else:
            st.write(f'N/A | {name}')

def load_suggestions(run_id):
    try:
        import pandas as pd
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(
            "SELECT * FROM prompt_suggestions WHERE run_id = ? ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END",
            conn, params=[run_id]
        )
        conn.close()
        return df
    except Exception:
        import pandas as pd
        return pd.DataFrame()


st.markdown("---")
tab1, tab2, tab3 = st.tabs(["Results", "Section Summary", "Prompt Suggestions"])

with tab1:
    st.subheader("Case results")
    filtered2 = df[df["overall_result"].isin(result_filter)] if result_filter else df
    filtered2 = filtered2.copy()
    filtered2["query_short"]    = filtered2["query"].str[:80]
    filtered2["response_short"] = filtered2["actual_response"].str[:80]
    display_cols = ["case_id", "section", "expected_action", "overall_result", "judge_score", "query_short", "response_short", "judge_reason"]
    st.dataframe(filtered2[display_cols].sort_values("case_id"), use_container_width=True, height=300, hide_index=True)
with tab2:
    st.subheader("Pass rate by section")
    all_df2 = load_results(selected_run)
    section_stats = all_df2.groupby("section").apply(
        lambda g: pd.Series({
            "total":     len(g),
            "pass":      (g["overall_result"] == "pass").sum(),
            "partial":   (g["overall_result"] == "partial").sum(),
            "fail":      (g["overall_result"] == "fail").sum(),
            "pass_rate": str(round((g["overall_result"] == "pass").sum() / len(g) * 100, 1)) + "%"
        })
    ).reset_index()
    st.dataframe(section_stats, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Prompt Improvement Suggestions")
    suggestions_df = load_suggestions(selected_run)
    if suggestions_df.empty:
        st.info("No suggestions yet for this run.")
        st.code(f"python prompt_engine.py --run-id {selected_run}")
    else:
        for priority in ["high", "medium", "low"]:
            subset = suggestions_df[suggestions_df["priority"] == priority]
            if not subset.empty:
                st.markdown(f"### {priority.capitalize()} priority")
                for _, s in subset.iterrows():
                    with st.expander(f"{s['rule']} — {s['failure_count']} failures"):
                        st.markdown(f"**Prompt section:** {s['prompt_section']}")
                        st.markdown(f"**Issue:** {s['issue']}")
                        st.success(f"**Suggested fix:** {s['suggestion']}")

st.markdown("---")
st.subheader("Run Summary")
total_all   = len(load_results(selected_run))
pass_all    = (load_results(selected_run)["overall_result"] == "pass").sum()
partial_all = (load_results(selected_run)["overall_result"] == "partial").sum()
fail_all    = (load_results(selected_run)["overall_result"] == "fail").sum()

st.markdown(f"""
**Run:** `{selected_run}`
**Total cases:** {total_all}
**Pass rate:** {round(pass_all/total_all*100) if total_all else 0}%
**Partial:** {round(partial_all/total_all*100) if total_all else 0}%
**Fail rate:** {round(fail_all/total_all*100) if total_all else 0}%

**Key findings:**
- Sections with most failures: {
    ', '.join(
        load_results(selected_run)
        .groupby("section")
        .apply(lambda g: (g["overall_result"] == "fail").sum())
        .sort_values(ascending=False)
        .head(3)
        .index.tolist()
    )
}
- Most common failing action: {
    load_results(selected_run)[load_results(selected_run)["overall_result"] == "fail"]["expected_action"].value_counts().index[0]
    if (load_results(selected_run)["overall_result"] == "fail").any() else "none"
}
""")