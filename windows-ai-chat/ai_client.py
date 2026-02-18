"""
ai_client.py — OpenAI API ラッパー
"""
import os

import openai
from openai import (
    OpenAI,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
    APIStatusError,
)

# temperature を渡すと壊れるモデル
_NO_TEMP_MODELS = frozenset({"o1", "o1-mini", "o1-preview", "o3", "o3-mini"})


class AIClient:
    """OpenAI Chat API クライアント"""

    def __init__(self, settings: dict):
        self.settings = settings

    def is_api_key_set(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY", "").strip())

    def chat(self, messages: list[dict]) -> str:
        """
        messages: [{"role": "user"|"assistant", "content": str}, ...]
        return: AIの返答テキスト
        raises: RuntimeError（ユーザー向けメッセージ付き）
        """
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY が設定されていません。\n"
                "環境変数を設定してアプリを再起動してください。"
            )

        client = OpenAI(api_key=api_key)
        model = self.settings.get("model", "gpt-4o-mini")

        # システムメッセージを先頭に追加
        full_messages: list[dict] = []
        system_msg = self.settings.get("system_message", "").strip()
        if system_msg:
            role = (
                "developer"
                if self.settings.get("use_developer_role", False)
                else "system"
            )
            full_messages.append({"role": role, "content": system_msg})
        full_messages.extend(messages)

        # API 呼び出しパラメータ
        params: dict = {"model": model, "messages": full_messages}
        if model not in _NO_TEMP_MODELS:
            params["temperature"] = float(self.settings.get("temperature", 0.7))

        try:
            response = client.chat.completions.create(**params)
            return response.choices[0].message.content or ""

        except AuthenticationError:
            raise RuntimeError(
                "APIキーが無効です。\n"
                "正しいキーを環境変数に設定してアプリを再起動してください。"
            )
        except RateLimitError:
            raise RuntimeError(
                "レートリミットに達しました。\n"
                "少し待ってから再送信してください。"
            )
        except APIConnectionError:
            raise RuntimeError(
                "ネットワーク接続エラーです。\n"
                "インターネット接続を確認してください。"
            )
        except APIStatusError as e:
            raise RuntimeError(
                f"OpenAI API エラー (HTTP {e.status_code}):\n{e.message}"
            )
        except Exception as e:
            raise RuntimeError(f"予期しないエラー:\n{e}")
