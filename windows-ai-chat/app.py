"""
app.py — AIチャット デスクトップアプリ (Python + Tkinter)
起動: python app.py
"""
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from ai_client import AIClient
from settings import SettingsDialog, load_settings
from storage import (
    append_text_log,
    list_history_dates,
    load_json_history,
    load_json_history_by_date,
    save_json_history,
)


# ========= カラー定数 =========

_C = {
    "bg":        "#f0f4ff",   # ウィンドウ背景
    "chat_bg":   "#ffffff",   # チャットエリア背景
    "input_bg":  "#f6f8ff",   # 入力エリア背景
    "user":      "#3d6fef",   # ユーザーラベル色
    "ai":        "#2a8a5a",   # AI ラベル色
    "error":     "#cc3333",   # エラー色
    "sub":       "#888888",   # サブテキスト色
    "border":    "#c8d0e8",   # ボーダー色
    "btn":       "#4b7cff",   # 送信ボタン
    "btn_hover": "#3a6bef",
    "copy_bg":   "#e8efff",
    "copy_fg":   "#4b7cff",
}

_FONT = "Meiryo"  # Windows 向け。Mac なら "Hiragino Sans" などに変更可


# ========= ヒストリブラウザ =========

class HistoryBrowser(tk.Toplevel):
    """過去の会話履歴を選択するモーダルダイアログ"""

    def __init__(self, parent: tk.Tk, dates: list[str], on_select):
        super().__init__(parent)
        self.title("過去の会話を読み込む")
        self.geometry("300x380")
        self.resizable(False, True)
        self.grab_set()

        self._dates = dates
        self._on_select = on_select

        ttk.Label(self, text="日付を選んでダブルクリック（または「読み込む」）", padding=8).pack(
            fill=tk.X
        )

        lf = ttk.Frame(self, padding=(8, 0, 8, 0))
        lf.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(lf)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._lb = tk.Listbox(lf, yscrollcommand=sb.set, font=(_FONT, 11), activestyle="dotbox")
        self._lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.configure(command=self._lb.yview)

        for d in dates:
            label = f"{d[:4]}/{d[4:6]}/{d[6:8]}" if len(d) == 8 else d
            self._lb.insert(tk.END, label)

        self._lb.bind("<Double-Button-1>", lambda _: self._load())

        bf = ttk.Frame(self, padding=(8, 6, 8, 10))
        bf.pack(fill=tk.X)
        ttk.Button(bf, text="読み込む", command=self._load).pack(side=tk.RIGHT, padx=4)
        ttk.Button(bf, text="キャンセル", command=self.destroy).pack(side=tk.RIGHT)

        self._center(parent)

    def _center(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + parent.winfo_width() // 2 - self.winfo_width() // 2
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _load(self) -> None:
        sel = self._lb.curselection()
        if not sel:
            return
        date_str = self._dates[sel[0]]
        self.destroy()
        self._on_select(date_str)


# ========= メインアプリ =========

class ChatApp:
    """メインチャットアプリケーション"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AIチャット ✦ 自分専用")
        self.root.geometry("820x660")
        self.root.minsize(520, 400)
        self.root.configure(bg=_C["bg"])

        # ── 状態 ──
        self._settings = load_settings()
        self._ai = AIClient(self._settings)
        self._messages: list[dict] = []   # OpenAI 形式の会話履歴
        self._sending = False
        self._last_ai_text: str = ""

        # ── UI 構築 ──
        self._build_menu()
        self._build_chat_area()
        self._build_input_area()
        self._build_statusbar()

        # ── 初期化 ──
        self._load_today_history()
        self.root.after(120, self._check_api_key)

    # ──────────────────────────────────────────
    # メニュー
    # ──────────────────────────────────────────

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # ファイル
        m = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="ファイル", menu=m)
        m.add_command(label="会話をクリア", command=self._clear_chat)
        m.add_command(label="過去の履歴を読み込む…", command=self._open_history_browser)
        m.add_separator()
        m.add_command(label="終了", command=self.root.quit)

        # 設定
        m = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="設定", menu=m)
        m.add_command(label="設定を開く…", command=self._open_settings)

        # ヘルプ
        m = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="ヘルプ", menu=m)
        m.add_command(label="使い方", command=self._show_help)

    # ──────────────────────────────────────────
    # チャットエリア
    # ──────────────────────────────────────────

    def _build_chat_area(self) -> None:
        outer = tk.Frame(self.root, bg=_C["bg"])
        outer.pack(fill=tk.BOTH, expand=True, padx=14, pady=(12, 0))

        # ヘッダー
        header = tk.Frame(outer, bg=_C["bg"])
        header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(
            header,
            text=datetime.now().strftime("%Y/%m/%d (%a)"),
            bg=_C["bg"], fg=_C["sub"],
            font=(_FONT, 9),
        ).pack(side=tk.LEFT)
        self._model_lbl = tk.Label(
            header,
            text=f"モデル: {self._settings['model']}",
            bg=_C["bg"], fg=_C["sub"],
            font=(_FONT, 9),
        )
        self._model_lbl.pack(side=tk.RIGHT)

        # テキストウィジェット
        tf = tk.Frame(
            outer, bg=_C["chat_bg"],
            highlightbackground=_C["border"], highlightthickness=1,
        )
        tf.pack(fill=tk.BOTH, expand=True)

        fs = self._settings.get("font_size", 12)
        self._chat = tk.Text(
            tf,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=_C["chat_bg"], fg="#1b1f2a",
            font=(_FONT, fs),
            relief=tk.FLAT,
            padx=14, pady=10,
            cursor="arrow",
            spacing3=4,
        )
        self._chat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(tf, command=self._chat.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._chat.configure(yscrollcommand=sb.set)

        self._configure_tags()

    def _configure_tags(self) -> None:
        fs = self._settings.get("font_size", 12)
        t = self._chat
        t.tag_configure("user_lbl",   foreground=_C["user"],  font=(_FONT, fs - 1, "bold"), spacing1=12)
        t.tag_configure("user_msg",   foreground="#1b1f2a",   lmargin1=18, lmargin2=18, spacing3=2)
        t.tag_configure("ai_lbl",     foreground=_C["ai"],    font=(_FONT, fs - 1, "bold"), spacing1=12)
        t.tag_configure("ai_msg",     foreground="#1b1f2a",   lmargin1=18, lmargin2=18, spacing3=2)
        t.tag_configure("error_lbl",  foreground=_C["error"], font=(_FONT, fs - 1, "bold"), spacing1=12)
        t.tag_configure("error_msg",  foreground=_C["error"], lmargin1=18, lmargin2=18, spacing3=2)
        t.tag_configure("sys_msg",    foreground=_C["sub"],   font=(_FONT, fs - 1, "italic"), justify=tk.CENTER, spacing1=6, spacing3=6)
        t.tag_configure("font_tag",   font=(_FONT, fs))

    # ──────────────────────────────────────────
    # 入力エリア
    # ──────────────────────────────────────────

    def _build_input_area(self) -> None:
        outer = tk.Frame(self.root, bg=_C["bg"])
        outer.pack(fill=tk.X, padx=14, pady=10)

        container = tk.Frame(
            outer, bg=_C["input_bg"],
            highlightbackground=_C["border"], highlightthickness=1,
        )
        container.pack(fill=tk.X)

        fs = self._settings.get("font_size", 12)
        self._input = tk.Text(
            container,
            height=3, wrap=tk.WORD,
            bg=_C["input_bg"], fg="#1b1f2a",
            font=(_FONT, fs),
            relief=tk.FLAT,
            padx=10, pady=8,
            insertbackground=_C["btn"],
        )
        self._input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ボタン群
        bf = tk.Frame(container, bg=_C["input_bg"])
        bf.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)

        self._send_btn = tk.Button(
            bf, text="送信",
            command=self._on_send,
            bg=_C["btn"], fg="white",
            font=(_FONT, 10, "bold"),
            relief=tk.FLAT, padx=16, pady=6,
            cursor="hand2",
            activebackground=_C["btn_hover"], activeforeground="white",
        )
        self._send_btn.pack(fill=tk.X)

        self._copy_btn = tk.Button(
            bf, text="最後をコピー",
            command=self._copy_last_response,
            bg=_C["copy_bg"], fg=_C["copy_fg"],
            font=(_FONT, 9),
            relief=tk.FLAT, padx=10, pady=4,
            cursor="hand2",
            activebackground="#d8e6ff",
        )
        self._copy_btn.pack(fill=tk.X, pady=(5, 0))

        tk.Label(
            outer,
            text="Enter で送信  /  Shift+Enter で改行",
            bg=_C["bg"], fg=_C["sub"],
            font=(_FONT, 8),
        ).pack(anchor=tk.E, pady=(2, 0))

        # キーバインド
        self._input.bind("<Return>", self._on_enter)
        self._input.bind("<Shift-Return>", self._on_shift_enter)
        self._input.focus_set()

    def _build_statusbar(self) -> None:
        self._status_var = tk.StringVar(value="準備完了")
        bar = tk.Label(
            self.root,
            textvariable=self._status_var,
            bg="#e0e6f8", fg=_C["sub"],
            font=(_FONT, 8),
            anchor=tk.W, padx=10, pady=2,
        )
        bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ──────────────────────────────────────────
    # チャット表示
    # ──────────────────────────────────────────

    def _write(self, text: str, *tags: str) -> None:
        self._chat.configure(state=tk.NORMAL)
        self._chat.insert(tk.END, text, tags)
        self._chat.configure(state=tk.DISABLED)
        self._chat.see(tk.END)

    def _append(self, role: str, content: str) -> None:
        """ロール別にメッセージを追記する。"""
        now = datetime.now().strftime("%H:%M")

        if role == "user":
            self._write(f"あなた  {now}\n", "user_lbl")
            self._write(content + "\n", "user_msg")
        elif role == "assistant":
            self._write(f"AI  {now}\n", "ai_lbl")
            self._write(content + "\n", "ai_msg")
            self._last_ai_text = content
        elif role == "error":
            self._write(f"エラー  {now}\n", "error_lbl")
            self._write(content + "\n", "error_msg")
        elif role == "system":
            self._write(content + "\n", "sys_msg")

    # ──────────────────────────────────────────
    # キーイベント
    # ──────────────────────────────────────────

    def _on_enter(self, _event) -> str:
        if not self._sending:
            self._on_send()
        return "break"  # デフォルト改行を抑制

    def _on_shift_enter(self, _event) -> None:
        return None  # 通常改行を許可

    # ──────────────────────────────────────────
    # 送信処理
    # ──────────────────────────────────────────

    def _on_send(self) -> None:
        if self._sending:
            return
        text = self._input.get("1.0", tk.END).strip()
        if not text:
            return

        self._input.delete("1.0", tk.END)
        self._append("user", text)
        self._messages.append({"role": "user", "content": text})

        try:
            append_text_log("user", text)
        except Exception as e:
            print(f"[log error] {e}")

        self._set_sending(True)
        threading.Thread(target=self._call_api, daemon=True).start()

    def _call_api(self) -> None:
        try:
            reply = self._ai.chat(self._messages)
            self.root.after(0, self._on_success, reply)
        except Exception as e:
            self.root.after(0, self._on_error, str(e))

    def _on_success(self, reply: str) -> None:
        self._messages.append({"role": "assistant", "content": reply})
        self._append("assistant", reply)
        try:
            append_text_log("assistant", reply)
            save_json_history(self._messages)
        except Exception as e:
            print(f"[log error] {e}")
        self._set_sending(False)
        self._status_var.set(f"返答受信 {datetime.now().strftime('%H:%M:%S')}")

    def _on_error(self, msg: str) -> None:
        # 送信失敗した user メッセージを履歴から除く（再送できるように）
        if self._messages and self._messages[-1]["role"] == "user":
            self._messages.pop()
        self._append("error", msg)
        self._set_sending(False)
        self._status_var.set("エラー発生")

    def _set_sending(self, sending: bool) -> None:
        self._sending = sending
        if sending:
            self._send_btn.configure(text="送信中…", state=tk.DISABLED, bg="#aaaaaa")
            self._status_var.set("AIが考えています…")
        else:
            self._send_btn.configure(text="送信", state=tk.NORMAL, bg=_C["btn"])
            self._input.focus_set()

    # ──────────────────────────────────────────
    # 履歴
    # ──────────────────────────────────────────

    def _load_today_history(self) -> None:
        msgs = load_json_history()
        if not msgs:
            self._append("system", "── 今日の会話をここから始めましょう ──")
            return
        self._messages = msgs
        self._append("system", "── 今日の保存済み会話を読み込みました ──")
        for m in msgs:
            if m.get("role") in ("user", "assistant"):
                self._append(m["role"], m.get("content", ""))

    def _open_history_browser(self) -> None:
        dates = list_history_dates()
        if not dates:
            messagebox.showinfo("履歴", "保存された履歴はありません。", parent=self.root)
            return
        HistoryBrowser(self.root, dates, self._load_selected_date)

    def _load_selected_date(self, date_str: str) -> None:
        msgs = load_json_history_by_date(date_str)
        if not msgs:
            messagebox.showinfo("履歴", "この日の履歴が見つかりませんでした。", parent=self.root)
            return
        label = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:8]}"
        if not messagebox.askyesno(
            "確認",
            f"{label} の履歴を読み込みますか？\n現在の会話はクリアされます。",
            parent=self.root,
        ):
            return
        self._clear_display()
        self._messages = msgs
        self._append("system", f"── {label} の履歴 ──")
        for m in msgs:
            if m.get("role") in ("user", "assistant"):
                self._append(m["role"], m.get("content", ""))

    def _clear_chat(self) -> None:
        if self._messages and not messagebox.askyesno(
            "確認", "現在の会話をクリアしますか？", parent=self.root
        ):
            return
        self._messages = []
        self._last_ai_text = ""
        self._clear_display()
        self._append("system", "── 会話をクリアしました ──")

    def _clear_display(self) -> None:
        self._chat.configure(state=tk.NORMAL)
        self._chat.delete("1.0", tk.END)
        self._chat.configure(state=tk.DISABLED)

    # ──────────────────────────────────────────
    # コピー
    # ──────────────────────────────────────────

    def _copy_last_response(self) -> None:
        if not self._last_ai_text:
            messagebox.showinfo("コピー", "コピーする AI の返答がありません。", parent=self.root)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self._last_ai_text)
        self._copy_btn.configure(text="コピー完了 ✓", bg="#c4f0c4")
        self.root.after(1600, lambda: self._copy_btn.configure(text="最後をコピー", bg=_C["copy_bg"]))

    # ──────────────────────────────────────────
    # 設定
    # ──────────────────────────────────────────

    def _open_settings(self) -> None:
        SettingsDialog(self.root, self._settings, on_save=self._apply_settings)

    def _apply_settings(self, new_settings: dict) -> None:
        self._settings = new_settings
        self._ai = AIClient(self._settings)
        self._model_lbl.configure(text=f"モデル: {new_settings['model']}")
        fs = new_settings.get("font_size", 12)
        self._chat.configure(font=(_FONT, fs))
        self._input.configure(font=(_FONT, fs))
        self._configure_tags()

    # ──────────────────────────────────────────
    # APIキーチェック
    # ──────────────────────────────────────────

    def _check_api_key(self) -> None:
        if self._ai.is_api_key_set():
            return
        self._append(
            "error",
            "OPENAI_API_KEY が設定されていません。\n\n"
            "【Windows PowerShell】\n"
            "  $env:OPENAI_API_KEY = 'sk-ここにキーを貼る'\n"
            "  python app.py\n\n"
            "【Windows コマンドプロンプト (CMD)】\n"
            "  set OPENAI_API_KEY=sk-ここにキーを貼る\n"
            "  python app.py",
        )
        messagebox.showwarning(
            "APIキー未設定",
            "環境変数 OPENAI_API_KEY が見つかりません。\n\n"
            "アプリは起動しますが、メッセージ送信時にエラーになります。\n\n"
            "環境変数を設定してアプリを再起動してください。",
            parent=self.root,
        )

    # ──────────────────────────────────────────
    # ヘルプ
    # ──────────────────────────────────────────

    def _show_help(self) -> None:
        messagebox.showinfo(
            "使い方",
            "【基本操作】\n"
            "  Enter          → 送信\n"
            "  Shift+Enter    → 改行\n"
            "  「最後をコピー」→ AIの最後の返答をクリップボードへ\n\n"
            "【メニュー】\n"
            "  ファイル > 会話をクリア        … 現在の会話を消去\n"
            "  ファイル > 過去の履歴を読み込む … 保存した日付を選んで復元\n"
            "  設定 > 設定を開く               … モデル / Temperature / 文字サイズ など\n\n"
            "【ログ保存場所】\n"
            "  logs/YYYYMMDD.txt   （テキスト形式）\n"
            "  logs/YYYYMMDD.json  （再読み込み用）\n\n"
            "【APIキーの設定】\n"
            "  PowerShell: $env:OPENAI_API_KEY = 'sk-...'\n"
            "  CMD:        set OPENAI_API_KEY=sk-...",
            parent=self.root,
        )


# ========= 起動 =========

def main() -> None:
    root = tk.Tk()
    ChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
