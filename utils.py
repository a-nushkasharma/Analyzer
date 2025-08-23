from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def coerce_json_list(raw: str) -> list:
    """Try to extract a JSON list from the raw LLM text; returns [] on failure."""
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        s = raw.find("["); e = raw.rfind("]")
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(raw[s:e+1])
            except Exception:
                return []
        return []

def load_prompt(name: str, base_dir: str = "prompt_templates") -> str:
    p = Path(base_dir) / f"{name}.txt"
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""

def save_json(obj: Any, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
