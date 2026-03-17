addition = """

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
    display_cols = ["case_id", "section", "expected_action", "scoring_method", "overall_result", "judge_score", "judge_reason"]
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
"""

with open("dashboard.py", "a") as f:
    f.write(addition)
print("dashboard.py patched OK")