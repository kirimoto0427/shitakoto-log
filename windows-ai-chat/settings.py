"""
settings.py — 設定管理 + 設定ダイアログ
"""
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

# スクリプトと同じ場所に保存
_CONFIG_PATH = Path(__file__).parent / "config.json"

# ========= デフォルト設定 =========

DEFAULT_SETTINGS: dict = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "system_message": "あなたは親切で役立つアシスタントです。",
    "use_developer_role": False,
    "font_size": 12,
    "kiri_mode": False,
}

KIRI_MODE_SYSTEM_MESSAGE = """\
あなたは「きりちゃん」のための個人アシスタントです。
以下のルールを守って会話してください。

- 返答は短め（3〜5文以内が目安）。押し付けない。
- 感情・事実・解釈・意味付けを分けて整理する。
- ADHDの特性を理解した上で、優しく寄り添う。
- 否定せず、選択肢を提示する。
- 断定よりも「〜かもしれない」「〜という見方もある」の形にする。\
"""

_MODEL_LIST = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "o1-mini",
    "o3-mini",
]


# ========= 設定 I/O =========

def load_settings() -> dict:
    """config.json を読み込み、デフォルトとマージして返す。"""
    settings = DEFAULT_SETTINGS.copy()
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            settings.update(saved)
        except Exception:
            pass  # 壊れていたらデフォルトのまま
    return settings


def save_settings(settings: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# ========= 設定ダイアログ =========

class SettingsDialog(tk.Toplevel):
    """設定画面（モーダル）"""

    def __init__(self, parent: tk.Tk, settings: dict, on_save=None):
        super().__init__(parent)
        self.title("設定")
        self.resizable(False, False)
        self.grab_set()  # モーダル化

        self._settings = settings.copy()
        self._on_save = on_save

        self._build_ui()
        self._center(parent)

    # ──────────────────────────────────────────
    # 配置

    def _center(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + parent.winfo_width() // 2 - self.winfo_width() // 2
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        PAD = {"padx": 12, "pady": 6}
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # ── モデル ──
        ttk.Label(frame, text="モデル:").grid(row=row, column=0, sticky="w", **PAD)
        self._model_var = tk.StringVar(value=self._settings["model"])
        ttk.Combobox(
            frame,
            textvariable=self._model_var,
            values=_MODEL_LIST,
            width=26,
        ).grid(row=row, column=1, sticky="ew", **PAD)
        row += 1

        # ── Temperature ──
        ttk.Label(frame, text="Temperature:").grid(row=row, column=0, sticky="w", **PAD)
        temp_frame = ttk.Frame(frame)
        temp_frame.grid(row=row, column=1, sticky="ew", **PAD)
        self._temp_var = tk.DoubleVar(value=self._settings["temperature"])
        self._temp_lbl = ttk.Label(
            temp_frame, text=f"{self._settings['temperature']:.1f}", width=4
        )
        ttk.Scale(
            temp_frame,
            from_=0.0,
            to=2.0,
            variable=self._temp_var,
            orient="horizontal",
            length=200,
            command=lambda v: self._temp_lbl.config(text=f"{float(v):.1f}"),
        ).pack(side=tk.LEFT)
        self._temp_lbl.pack(side=tk.LEFT, padx=4)
        row += 1

        # ── 文字サイズ ──
        ttk.Label(frame, text="文字サイズ:").grid(row=row, column=0, sticky="w", **PAD)
        self._font_size_var = tk.IntVar(value=self._settings["font_size"])
        ttk.Spinbox(
            frame, from_=8, to=24, textvariable=self._font_size_var, width=6
        ).grid(row=row, column=1, sticky="w", **PAD)
        row += 1

        # ── きりちゃんモード ──
        ttk.Label(frame, text="きりちゃんモード:").grid(row=row, column=0, sticky="w", **PAD)
        self._kiri_var = tk.BooleanVar(value=self._settings["kiri_mode"])
        ttk.Checkbutton(
            frame,
            variable=self._kiri_var,
            text="有効にする（専用プリセットを使用）",
            command=self._on_kiri_toggle,
        ).grid(row=row, column=1, sticky="w", **PAD)
        row += 1

        # ── developer ロール ──
        ttk.Label(frame, text="developerロール:").grid(row=row, column=0, sticky="w", **PAD)
        self._dev_role_var = tk.BooleanVar(value=self._settings["use_developer_role"])
        ttk.Checkbutton(
            frame,
            variable=self._dev_role_var,
            text="system の代わりに developer を使用",
        ).grid(row=row, column=1, sticky="w", **PAD)
        row += 1

        # ── システムメッセージ ──
        ttk.Label(frame, text="システムメッセージ:").grid(
            row=row, column=0, sticky="nw", **PAD
        )
        sys_frame = ttk.Frame(frame)
        sys_frame.grid(row=row, column=1, sticky="nsew", **PAD)
        self._sys_text = tk.Text(sys_frame, width=40, height=7, wrap=tk.WORD)
        sys_scroll = ttk.Scrollbar(sys_frame, command=self._sys_text.yview)
        self._sys_text.configure(yscrollcommand=sys_scroll.set)
        self._sys_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sys_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._sys_text.insert("1.0", self._settings["system_message"])
        row += 1

        frame.columnconfigure(1, weight=1)

        # ── ボタン ──
        btn_frame = ttk.Frame(self, padding=(16, 0, 16, 16))
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side=tk.RIGHT)

    def _on_kiri_toggle(self) -> None:
        if self._kiri_var.get():
            self._sys_text.delete("1.0", tk.END)
            self._sys_text.insert("1.0", KIRI_MODE_SYSTEM_MESSAGE)

    def _save(self) -> None:
        self._settings["model"] = self._model_var.get()
        self._settings["temperature"] = round(float(self._temp_var.get()), 1)
        self._settings["font_size"] = self._font_size_var.get()
        self._settings["kiri_mode"] = self._kiri_var.get()
        self._settings["use_developer_role"] = self._dev_role_var.get()
        self._settings["system_message"] = self._sys_text.get("1.0", tk.END).strip()
        save_settings(self._settings)
        if self._on_save:
            self._on_save(self._settings)
        self.destroy()
