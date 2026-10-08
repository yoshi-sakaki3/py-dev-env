"""Claude API で文章を要約するサンプル

ANTHROPIC_API_KEY（または `ant auth login` のプロファイル）があれば動く。
無い環境では呼び出し側で「未設定」と返す。
"""

import os

import anthropic

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = (
    "あなたは日本語の文章を要約するアシスタントです。"
    "入力された文章の要点を、3つ以内の箇条書きで、短く正確にまとめてください。"
    "文章に書かれていないことは付け足さないでください。"
)


class SummaryRefusedError(Exception):
    """モデルが要約を断ったとき"""


def has_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def summarize(text: str, client: anthropic.Anthropic | None = None) -> str:
    client = client or anthropic.Anthropic()
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        # 要約は軽い作業なので effort は low（Claude Opus 5.5 の既定は medium）
        output_config={"effort": "low"},
        # 安全上の理由で断られたときに、サーバー側で自動的に別のモデルへ切り替える
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    if response.stop_reason == "refusal":
        raise SummaryRefusedError("この文章は要約できませんでした。")
    return "".join(block.text for block in response.content if block.type == "text").strip()
