import pandas as pd

def load_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    cols = {c.lower(): c for c in df.columns}
    t_col = cols.get("t") or cols.get("time") or cols.get("timestamp") or df.columns[0]
    x_col = cols.get("x") or cols.get("value") or cols.get("price") or df.columns[1]
    out = df[[t_col, x_col]].copy()
    out.columns = ["t", "x"]
    return out
