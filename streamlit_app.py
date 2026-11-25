"""Streamlit front end for gold-checker. Run with: streamlit run streamlit_app.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from gold_checker import __version__, load_items, run_check  # noqa: E402
from gold_checker.compare import DISAGREE, UNREADABLE  # noqa: E402
from gold_checker.datasets import DATASETS, fetch  # noqa: E402
from gold_checker.report import to_csv, to_json, to_markdown  # noqa: E402

ZENODO = 'https://doi.org/10.5281/zenodo.24520462'
ORCID = 'https://orcid.org/0009-0001-9453-0226'
SAMPLE = ROOT / 'examples' / 'sample.csv'

st.set_page_config(page_title='Gold-answer checker', layout='wide')
st.title('Gold-answer checker')
st.caption('Reruns each benchmark item\'s gold program and flags items whose written gold answer '
           'disagrees with it. A model scored against those items is graded against the wrong answer.')

with st.sidebar:
    st.header('Data')
    choice = st.radio('Benchmark', ['Sample file (10 made-up items)'] +
                      [d['label'] for d in DATASETS.values()] + ['Upload my own file'])
    upload = None
    if choice == 'Upload my own file':
        upload = st.file_uploader('JSON, JSONL or CSV', type=['json', 'jsonl', 'csv'])
        st.caption('FinQA and ConvFinQA files are read as they ship. For any other benchmark, use one row '
                   'per item with columns id, answer, and program (FinQA style) and/or exe_ans (stored '
                   'gold value). Optional: question, table, page.')
    st.header('Settings')
    tol_pct = st.slider('Relative tolerance (%)', 0.0, 5.0, 0.5, 0.1,
                        help='Written answers are first compared at the precision they are written '
                             '("14.1%" matches 0.14096). This tolerance is the fallback.')

@st.cache_data(show_spinner='Downloading the benchmark from its GitHub repository...')
def dataset_path(name):
    return str(fetch(name))


def load():
    if choice.startswith('Sample'):
        return load_items(SAMPLE), 'sample.csv'
    if choice == 'Upload my own file':
        if upload is None:
            return None, None
        return load_items(upload.getvalue(), upload.name), upload.name
    name = next(k for k, d in DATASETS.items() if d['label'] == choice)
    return load_items(Path(dataset_path(name))), choice


try:
    loaded, source = load()
except Exception as err:  # bad upload: show it instead of a stack trace
    st.error(f'Could not read that file: {err}')
    st.stop()
if loaded is None:
    st.info('Choose a file to check.')
    st.stop()

items, fmt = loaded
try:
    report = run_check(items, fmt=fmt, source=source, rel_tol=tol_pct / 100)
except Exception as err:  # an item the checker cannot handle: say so instead of a stack trace
    st.error(f'Could not check that file: {err}')
    st.stop()
s = report.summary()

c = st.columns(5)
c[0].metric('Items checked', f"{s['items']:,}")
c[1].metric('Answer disagrees with gold', s['disagree'])
c[2].metric('Answer empty or not a number', s['unreadable'])
c[3].metric('Program ≠ stored value', s['program_vs_stored'])
c[4].metric('Program would not run', s['program_errors'])
share = s['disagree'] / s['items'] if s['items'] else 0
line = f"**{s['disagree']} of {s['items']:,} items ({share:.1%})** have a written gold answer that disagrees with the gold value."
if s.get('unique_questions'):
    u = s['unique_questions']
    line += (f" Counting each page-question pair once: {u['flagged']} of {u['questions']:,} unique questions "
             f"flagged ({u['disagree']} disagree, {u['unreadable']} empty or not a number).")
st.markdown(line)
if s['format_notes']:
    st.caption(f"{s['format_notes']} more items write a correct number with a percent-sign slip; those are "
               'counted as format notes, not errors.')

kinds = {**s['disagree_by_kind'], **s['unreadable_by_kind']}
if kinds:
    st.subheader('What kind of disagreement')
    st.bar_chart(pd.DataFrame({'items': kinds}), horizontal=True)

st.subheader('Flagged items')
rows = pd.DataFrame([r.row() for r in report.flagged])
for col in ('written_answer', 'gold_value', 'executed'):
    if col in rows:
        rows[col] = rows[col].astype(str)
if rows.empty:
    st.success('Nothing flagged.')
else:
    pick = st.multiselect('Show kinds', [k for k in DISAGREE + UNREADABLE if k in kinds] + ['program'],
                          default=[k for k in DISAGREE if k in kinds] or None)
    view = rows
    if pick:
        mask = rows['kind'].isin(pick)
        if 'program' in pick:
            mask |= rows['program_vs_stored'] | (rows['error'] != '')
        view = rows[mask]
    st.dataframe(view[['id', 'kind', 'written_answer', 'gold_value', 'question', 'program', 'page', 'error']],
                 hide_index=True, width='stretch')
    with st.expander('Look at one item'):
        sel = st.selectbox('Item', view['id'].tolist())
        if sel:
            r = next(x for x in report.flagged if x.item.id == sel)
            st.markdown(f"**Question:** {r.item.question}")
            st.markdown(f"**Written gold answer:** `{r.item.answer}` &nbsp; **Gold value:** `{r.compared_with}` "
                        f"&nbsp; **Program result:** `{r.executed}` &nbsp; **Verdict:** {r.kind or r.status}")
            st.code(r.item.program or '(no program)', language=None)
            if r.item.table:
                st.dataframe(pd.DataFrame(r.item.table).astype(str), hide_index=True)

st.subheader('Download')
d = st.columns(3)
stem = Path(source).stem.replace(' ', '_')
d[0].download_button('Flagged items (CSV)', to_csv(report), f'{stem}_flagged.csv', 'text/csv')
d[1].download_button('Full report (JSON)', to_json(report), f'{stem}_report.json', 'application/json')
d[2].download_button('Summary (Markdown)', to_markdown(report), f'{stem}_summary.md', 'text/markdown')

st.divider()
st.caption(f'gold-checker {__version__}. Built by Michael T. Varman, Morphogenesis Analytics '
           f'([ORCID 0009-0001-9453-0226]({ORCID})). The method and the hand-checked findings are in '
           f'"Gold-Answer Errors in Financial Numerical-Reasoning Benchmarks" ([Zenodo]({ZENODO})). '
           'Benchmark files are downloaded from their own repositories and are not redistributed here.')
