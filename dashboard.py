import streamlit as st
import sqlite3
import pandas as pd
import json
import plotly.express as px
from config import DB_PATH
from db import get_trend_data

st.set_page_config(page_title='Connie Eval Dashboard', layout='wide')
st.title('Connie Evaluator Dashboard')

SECTION_LABELS = {
    "A": "A — Greetings & Opening",
    "B": "B — Slot Filling: Location",
    "C": "C — Slot Filling: Dates",
    "D": "D — Slot Filling: Party Size",
    "E": "E — Slot Filling: Budget",
    "F": "F — Search Trigger",
    "G": "G — Pre-Search Summary",
    "H": "H — Scope Boundaries",
    "I": "I — Property Detail Queries",
    "J": "J — Truthfulness & Deferral",
    "K": "K — Jailbreak Resistance",
    "L": "L — Tone of Voice",
    "M": "M — One-Question Rule",
    "N": "N — Escalation",
    "O": "O — Contextual Inference",
}

def label(s):
    return SECTION_LABELS.get(s, s)

def get_run_ids():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(
            'SELECT DISTINCT run_id, MAX(created_at) as run_at '
            'FROM eval_results GROUP BY run_id ORDER BY run_at DESC', conn)
        conn.close()
        return df['run_id'].tolist()
    except Exception:
        return []

def load_results(run_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM eval_results WHERE run_id = ?', conn, params=[run_id])
    conn.close()
    return df

def load_suggestions(run_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(
            "SELECT * FROM prompt_suggestions WHERE run_id = ? "
            "ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END",
            conn, params=[run_id])
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def section_summary(df):
    return df.groupby('section').apply(
        lambda g: pd.Series({
            'section_name': label(g.name),
            'total':     len(g),
            'pass':      (g['overall_result'] == 'pass').sum(),
            'partial':   (g['overall_result'] == 'partial').sum(),
            'fail':      (g['overall_result'] == 'fail').sum(),
            'pass_rate': str(round((g['overall_result'] == 'pass').sum() / len(g) * 100, 1)) + '%'
        }), include_groups=False
    ).reset_index(drop=True)

# ── Sidebar ───────────────────────────────────────────────────────────
run_ids = get_run_ids()
if not run_ids:
    st.warning('No eval runs found. Run: python pipeline.py --limit 5 --dry-run')
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

result_filter = st.sidebar.multiselect(
    'Show results', ['pass', 'partial', 'fail', 'error'],
    default=['pass', 'partial', 'fail', 'error'])

# ── KPI metrics ───────────────────────────────────────────────────────
total   = len(df)
passed  = (df['overall_result'] == 'pass').sum()
partial = (df['overall_result'] == 'partial').sum()
failed  = (df['overall_result'] == 'fail').sum()
errors  = (df['overall_result'] == 'error').sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric('Total',   total)
col2.metric('Pass',    f'{passed} ({round(passed/total*100) if total else 0}%)')
col3.metric('Partial', f'{partial} ({round(partial/total*100) if total else 0}%)')
col4.metric('Fail',    f'{failed} ({round(failed/total*100) if total else 0}%)')
col5.metric('Error',   errors)

# ── Section summary ───────────────────────────────────────────────────
st.markdown('---')
st.subheader('Pass rate by section')
all_df = load_results(selected_run)
st.dataframe(section_summary(all_df), use_container_width=True, hide_index=True)

# ── Case drilldown ────────────────────────────────────────────────────
st.markdown('---')
st.subheader('Case drilldown')
filtered = df[df['overall_result'].isin(result_filter)] if result_filter else df
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
        'One-question rule': (row['det_one_q_score'],     row['det_one_q_result']),
        'Search trigger':    (row['det_search_score'],    row['det_search_result']),
        'Summary fields':    (row['det_summary_score'],   row['det_summary_result']),
        'Jailbreak resist':  (row['det_jailbreak_score'], row['det_jailbreak_result']),
    }
    for name, (score, result) in checks.items():
        if result and result != 'skip':
            icon = 'PASS' if result == 'pass' else 'PARTIAL' if result == 'partial' else 'FAIL'
            st.write(f'{icon} | {name}: score={score}')
        else:
            st.write(f'N/A | {name}')

# ── Tabs ──────────────────────────────────────────────────────────────
st.markdown('---')
tab1, tab2, tab3, tab4 = st.tabs(['Results', 'Section Summary', 'Prompt Suggestions', 'Tone of Voice Lab'])

with tab1:
    st.subheader('Case results')
    filtered2 = df[df['overall_result'].isin(result_filter)] if result_filter else df
    filtered2 = filtered2.copy()
    filtered2['section_name']   = filtered2['section'].apply(label)
    filtered2['query_short']    = filtered2['query'].str[:80]
    filtered2['response_short'] = filtered2['actual_response'].str[:80]
    display_cols = ['case_id', 'section_name', 'expected_action', 'overall_result',
                    'judge_score', 'query_short', 'response_short', 'judge_reason']
    st.dataframe(filtered2[display_cols].sort_values('case_id'),
                 use_container_width=True, height=300, hide_index=True)

with tab2:
    st.subheader('Pass rate by section')
    all_df2 = load_results(selected_run)
    st.dataframe(section_summary(all_df2), use_container_width=True, hide_index=True)

with tab3:
    st.subheader('Prompt Improvement Suggestions')
    suggestions_df = load_suggestions(selected_run)
    if suggestions_df.empty:
        st.info('No suggestions yet for this run.')
        st.code(f'python prompt_engine.py --run-id {selected_run}')
    else:
        for priority in ['high', 'medium', 'low']:
            subset = suggestions_df[suggestions_df['priority'] == priority]
            if not subset.empty:
                st.markdown(f'### {priority.capitalize()} priority')
                for _, s in subset.iterrows():
                    with st.expander(f"{s['rule']} — {s['failure_count']} failures"):
                        st.markdown(f"**Prompt section:** {s['prompt_section']}")
                        st.markdown(f"**Issue:** {s['issue']}")
                        st.success(f"**Suggested fix:** {s['suggestion']}")
with tab4:
    st.subheader('Tone of Voice Lab')
    st.caption('Step 1: Generate a revision based on failing cases. Step 2: Run Judge to compare. Step 3: Save if better.')

    import anthropic as ant
    import os

    # ── Load current prompt ───────────────────────────────────────
    try:
        with open('prompts/tov_prompt.md', encoding='utf-8') as f:
            current_prompt = f.read()
    except FileNotFoundError:
        current_prompt = ""

    # ── Session state for generated revision ─────────────────────
    if 'generated_revision' not in st.session_state:
        st.session_state.generated_revision = current_prompt

    # ── Pull failing cases ────────────────────────────────────────
    tov_fails = load_results(selected_run)
    tov_fails = tov_fails[tov_fails['overall_result'].isin(['fail', 'partial'])]
    n_fails = len(tov_fails)
    st.markdown(f'**{n_fails} failing/partial cases** in selected run.')

    max_cases = st.slider(
        'Number of cases to use',
        min_value=1,
        max_value=min(20, max(1, n_fails)),
        value=min(8, max(1, n_fails))
    )
    sample = tov_fails.head(max_cases)

    # ── Step 1: Generate revision ─────────────────────────────────
    st.markdown('### Step 1 — Generate revision')
    if st.button('Generate revision', disabled=(n_fails == 0)):
        from config import ANTHROPIC_API_KEY as api_key
        if not api_key:
            st.error('ANTHROPIC_API_KEY not set')
        else:
            client = ant.Anthropic(api_key=api_key)
            cases_text = "\n\n".join([
                f"Case {r['case_id']} ({label(r['section'])}):\n"
                f"  Query: {r['query']}\n"
                f"  Expected action: {r['expected_action']}\n"
                f"  Pass criteria: {r.get('pass_criteria','')}\n"
                f"  Fail criteria: {r.get('fail_criteria','')}\n"
                f"  Actual response: {str(r['actual_response'])[:300]}\n"
                f"  Judge reason: {r['judge_reason']}"
                for _, r in sample.iterrows()
            ])

            generate_prompt = f"""You are a prompt engineer improving a tone of voice prompt for Connie, a UK holiday cottage booking assistant for Sykes Holidays.

Here is the current prompt:
{current_prompt}

Here are {len(sample)} failing evaluation cases showing where Connie is not meeting expectations:
{cases_text}

Your task:
1. Identify the specific patterns causing failures
2. Produce a revised version of the full prompt that addresses these failures
3. Keep everything that is working — only change what needs to change
4. Do not add unnecessary length
5. Return ONLY the revised prompt text, no explanation, no preamble"""

            with st.spinner('Generating revision...'):
                try:
                    resp = client.messages.create(
                        model='claude-sonnet-4-20250514',
                        max_tokens=2000,
                        messages=[{'role': 'user', 'content': generate_prompt}]
                    )
                    st.session_state.generated_revision = resp.content[0].text.strip()
                    st.success('Revision generated. Review it in the panel below, then run the judge.')
                except Exception as e:
                    st.error(f'Generation failed: {e}')

    # ── Side by side prompt panels ────────────────────────────────
    st.markdown('### Step 2 — Review & edit')
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('**Current prompt**')
        current_display = st.text_area(
            'current_prompt_area',
            value=current_prompt,
            height=400,
            label_visibility='collapsed'
        )
    with col2:
        st.markdown('**Proposed revision**')
        proposed_display = st.text_area(
            'proposed_prompt_area',
            value=st.session_state.generated_revision,
            height=400,
            label_visibility='collapsed'
        )

    # ── Step 3: Run judge ─────────────────────────────────────────
    st.markdown('### Step 3 — Run judge')
    if st.button('Run Judge', disabled=(n_fails == 0)):
        from config import ANTHROPIC_API_KEY as api_key
        if not api_key:
            st.error('ANTHROPIC_API_KEY not set')
        else:
            client = ant.Anthropic(api_key=api_key)
            results = []

            with st.spinner(f'Judging {len(sample)} cases...'):
                for _, row in sample.iterrows():
                    judge_prompt = f"""You are evaluating two versions of a tone of voice prompt for Connie, a holiday booking assistant for Sykes Holidays.

CURRENT PROMPT:
{current_display}

PROPOSED PROMPT:
{proposed_display}

TEST CASE:
User query: {row['query']}
Connie's actual response: {row['actual_response']}
Expected action: {row['expected_action']}
Pass criteria: {row.get('pass_criteria', '')}
Fail criteria: {row.get('fail_criteria', '')}

Which prompt version would better produce the expected behaviour for this case?
Respond in JSON only:
{{
  "winner": "current" or "proposed" or "tie",
  "reason": "one sentence explanation",
  "current_score": 1,
  "proposed_score": 1
}}"""
                    try:
                        resp = client.messages.create(
                            model='claude-sonnet-4-20250514',
                            max_tokens=300,
                            messages=[{'role': 'user', 'content': judge_prompt}]
                        )
                        raw = resp.content[0].text.strip()
                        if raw.startswith('```'):
                            raw = '\n'.join(raw.split('\n')[1:-1])
                        verdict = json.loads(raw)
                        verdict['case_id'] = row['case_id']
                        verdict['section'] = label(row['section'])
                        verdict['query']   = row['query'][:80]
                        results.append(verdict)
                    except Exception as e:
                        results.append({
                            'case_id': row['case_id'],
                            'section': label(row['section']),
                            'query':   row['query'][:80],
                            'winner':  'error',
                            'reason':  str(e),
                            'current_score': None,
                            'proposed_score': None
                        })

            winners = [r['winner'] for r in results if r['winner'] != 'error']
            current_wins  = winners.count('current')
            proposed_wins = winners.count('proposed')
            ties          = winners.count('tie')

            st.markdown('---')
            st.markdown('### Verdict')
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric('Current wins',  current_wins)
            mc2.metric('Proposed wins', proposed_wins)
            mc3.metric('Ties',          ties)

            if proposed_wins > current_wins:
                st.success('Proposed prompt performs better on these cases.')
            elif current_wins > proposed_wins:
                st.warning('Current prompt performs better — reconsider the revision.')
            else:
                st.info('Too close to call — try more cases.')

            results_df = pd.DataFrame(results)
            st.dataframe(
                results_df[['case_id', 'section', 'query', 'winner',
                             'current_score', 'proposed_score', 'reason']],
                use_container_width=True, hide_index=True)

            # ── Step 4: Save ──────────────────────────────────────
            st.markdown('### Step 4 — Save')
            if proposed_wins > current_wins:
                if st.button('Save proposed as current prompt'):
                    with open('prompts/tov_prompt.md', 'w', encoding='utf-8') as f:
                        f.write(proposed_display)
                    st.session_state.generated_revision = proposed_display
                    st.success('Saved locally. Run: git add prompts/tov_prompt.md && git commit -m "Update ToV prompt" && git push origin main')
            else:
                st.info('Proposed did not outperform current — nothing saved.')
                
# ── Run summary ───────────────────────────────────────────────────────
st.markdown('---')
st.subheader('Run Summary')
all_results = load_results(selected_run)
total_all   = len(all_results)
pass_all    = (all_results['overall_result'] == 'pass').sum()
partial_all = (all_results['overall_result'] == 'partial').sum()
fail_all    = (all_results['overall_result'] == 'fail').sum()
top_fail_sections = (
    all_results.groupby('section')['overall_result']
    .apply(lambda x: (x == 'fail').sum())
    .sort_values(ascending=False)
    .head(3)
    .index.map(label)
    .tolist()
)
fail_actions = all_results[all_results['overall_result'] == 'fail']['expected_action']
most_common_action = fail_actions.value_counts().index[0] if not fail_actions.empty else 'none'

st.markdown(f"""
**Run:** `{selected_run}`  
**Total cases:** {total_all}  
**Pass rate:** {round(pass_all/total_all*100) if total_all else 0}%  
**Partial:** {round(partial_all/total_all*100) if total_all else 0}%  
**Fail rate:** {round(fail_all/total_all*100) if total_all else 0}%  

**Key findings:**  
- Sections with most failures: {', '.join(top_fail_sections)}  
- Most common failing action: {most_common_action}
""")

# ── Trend chart ───────────────────────────────────────────────────────
st.markdown('---')
st.subheader('Pass Rate Across Iterations')
trend_df = get_trend_data()

if trend_df.empty:
    st.info('No iteration data yet. Re-run the pipeline with --iteration to start tracking.')
else:
    fig = px.line(
        trend_df,
        x='iteration',
        y='pass_rate',
        color='dataset',
        markers=True,
        labels={'pass_rate': 'Pass Rate (%)', 'iteration': 'Prompt Version'},
        title='Connie Eval Pass Rate by Iteration'
    )
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        trend_df[['iteration', 'dataset', 'total', 'pass_rate', 'created_at']],
        use_container_width=True)