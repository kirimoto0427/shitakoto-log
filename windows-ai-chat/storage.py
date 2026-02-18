"""
storage.py — 会話ログ保存・読み込み

保存場所:
  logs/YYYYMMDD.txt   テキストログ（人間が読める形式）
  logs/YYYYMMDD.json  JSON 形式の会話履歴（再読み込み用）
"""
import json
from datetime import datetime
from pathlib import Path

# スクリプトと同じディレクトリの logs/ に保存
_LOGS_DIR = Path(__file__).parent / "logs"


# ========= ユーティリティ =========

def _ensure_logs_dir() -> None:
    _LOGS_DIR.mkdir(exist_ok=True)


def _today() -> str:
    return datetime.now().strftime("%Y%m%d")


def _txt_path(date: str = "") -> Path:
    return _LOGS_DIR / f"{date or _today()}.txt"


def _json_path(date: str = "") -> Path:
    return _LOGS_DIR / f"{date or _today()}.json"


# ========= テキストログ =========

def append_text_log(role: str, content: str) -> None:
    """1 件のメッセージをテキストファイルに追記する。"""
    _ensure_logs_dir()
    now = datetime.now().strftime("%H:%M:%S")
    label = "あなた" if role == "user" else "AI"
    with open(_txt_path(), "a", encoding="utf-8") as f:
        f.write(f"[{now}] {label}:\n{content}\n\n")


# ========= JSON 履歴 =========

def save_json_history(messages: list[dict]) -> None:
    """会話全体を今日の JSON ファイルに上書き保存する。"""
    _ensure_logs_dir()
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "messages": messages,
    }
    with open(_json_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json_history(date: str = "") -> list[dict]:
    """今日（または指定日）の JSON 履歴を読み込む。失敗時は空リスト。"""
    path = _json_path(date)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("messages", [])
    except Exception:
        return []


def list_history_dates() -> list[str]:
    """保存済み JSON ファイルの日付文字列一覧（新しい順）を返す。"""
    _ensure_logs_dir()
    dates = sorted(
        (p.stem for p in _LOGS_DIR.glob("*.json")),
        reverse=True,
    )
    return dates


def load_json_history_by_date(date_str: str) -> list[dict]:
    return load_json_history(date_str)
