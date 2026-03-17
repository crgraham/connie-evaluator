# CONNIE EVALUATOR — HOW TO START

1. Open this folder in Cursor
2. Open Terminal and run:
      source venv/bin/activate

3. Then run evals:
      python pipeline.py --limit 5 --section F   # quick test
      python pipeline.py --section F              # full section
      python pipeline.py                          # all 279 cases

4. Launch dashboard:
      streamlit run dashboard.py
