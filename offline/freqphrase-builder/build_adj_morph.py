#!/usr/bin/env python3
import sys
import json
from pathlib import Path

LEXICON_A1 = Path("data/es.lexicon.A1.json")
OUT_FILE = Path("data/es.adj.A1.morph.json")

def make_adj_forms(adj: str):
    # базовые A1-правила
    if adj.endswith("o"):
        base = adj[:-1]
        return {
            "m_sg": adj,
            "f_sg": base + "a",
            "m_pl": base + "os",
            "f_pl": base + "as"
        }
    elif adj.endswith("a"):
        base = adj[:-1]
        return {
            "m_sg": adj,   # grande-case handled separately
            "f_sg": adj,
            "m_pl": adj + "s",
            "f_pl": adj + "s"
        }
    else:
        # -e, -l, -r: одинаковый род
        return {
            "m_sg": adj,
            "f_sg": adj,
            "m_pl": adj + "s",
            "f_pl": adj + "s"
        }

def main():
    data = json.loads(LEXICON_A1.read_text(encoding="utf-8"))
    adjs = data.get("ADJ", [])

    result = {}
    for adj in adjs:
        result[adj] = make_adj_forms(adj)

    OUT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written: {OUT_FILE}")

if __name__ == "__main__":
    main()
