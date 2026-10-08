"""見積・請求で使う金額計算（テストの書き方のサンプルを兼ねる）"""

TAX_PERCENT = 10
"""消費税率（%）。小数の誤差を避けるため整数で持つ"""


def with_tax(amount: int) -> int:
    """税抜金額から税込金額を出す（1円未満は切り捨て）"""
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise ValueError("金額は0以上の整数にしてください。")
    return amount * (100 + TAX_PERCENT) // 100


def format_yen(amount: int) -> str:
    """3桁ごとにカンマを入れて「円」を付ける"""
    return f"{amount:,}円"
