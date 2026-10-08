"""環境チェック画面（http://localhost:8000）と API のサンプル

Python・DB 接続・メール送信・Claude API が動くかを1画面で確かめる。
API の説明は http://localhost:8000/docs（FastAPI が自動で作る）。
"""

import os
import platform
import smtplib
from datetime import datetime
from email.message import EmailMessage
from html import escape
from pathlib import Path
from string import Template

import anthropic
import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from app import ai

app = FastAPI(title="GLDX Python サンプル", version="1.0.0")


def check_db() -> tuple[bool, str]:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return False, "DATABASE_URL が設定されていません"
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            version = conn.execute("SELECT version()").fetchone()[0]
        return True, version.split(" on ")[0]
    except Exception as e:  # 画面に理由を出すため、ここでは広く受ける
        return False, str(e)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "python": platform.python_version()}


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000, description="要約したい文章")


class SummarizeResponse(BaseModel):
    summary: str
    model: str


@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest) -> SummarizeResponse:
    """Claude API で文章を要約する（ANTHROPIC_API_KEY が必要）"""
    if not ai.has_credentials():
        raise HTTPException(503, "ANTHROPIC_API_KEY が設定されていません（.env に書いて再起動）")
    try:
        summary = ai.summarize(req.text)
    except ai.SummaryRefusedError as e:
        raise HTTPException(422, str(e)) from e
    except anthropic.AuthenticationError as e:
        raise HTTPException(503, "API キーが無効です") from e
    except anthropic.RateLimitError as e:
        raise HTTPException(429, "利用上限に達しました。少し待ってから試してください") from e
    except anthropic.APIConnectionError as e:
        raise HTTPException(502, "Claude API に接続できませんでした") from e
    except anthropic.APIStatusError as e:
        raise HTTPException(502, f"Claude API のエラー（{e.status_code}）") from e
    return SummarizeResponse(summary=summary, model=ai.MODEL)


@app.post("/mail")
def send_mail() -> RedirectResponse:
    msg = EmailMessage()
    msg["From"] = "dev@example.com"
    msg["To"] = "test@example.com"
    msg["Subject"] = "テストメール"
    msg.set_content(f"Python 開発環境からのテスト送信です。\n{datetime.now():%Y-%m-%d %H:%M:%S}")
    host = os.environ.get("SMTP_HOST", "mailpit")
    port = int(os.environ.get("SMTP_PORT", "1025"))
    with smtplib.SMTP(host, port, timeout=5) as smtp:
        smtp.send_message(msg)
    return RedirectResponse("/?mail=sent", status_code=303)


TEMPLATE = Template((Path(__file__).parent / "templates" / "index.html").read_text("utf-8"))


@app.get("/", response_class=HTMLResponse)
def index(mail: str | None = Query(default=None)) -> str:
    db_ok, db_detail = check_db()
    ai_ok = ai.has_credentials()
    return TEMPLATE.substitute(
        python_version=escape(platform.python_version()),
        db_class="ok" if db_ok else "ng",
        db_status="接続できました" if db_ok else "接続できません",
        db_detail=escape(db_detail),
        mail_message=(
            "<p>送信しました。Mailpit（http://localhost:8027）で確認できます。</p>"
            if mail == "sent"
            else ""
        ),
        ai_class="ok" if ai_ok else "mute",
        ai_status=(
            "API キーが設定されています"
            if ai_ok
            else "API キーは未設定です（.env の ANTHROPIC_API_KEY）"
        ),
        model=escape(ai.MODEL),
    )
