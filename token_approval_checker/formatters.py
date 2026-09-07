import json
from typing import Sequence
from token_approval_checker.models import AllowanceRecord


def format_json(records: Sequence[AllowanceRecord], indent: int = 2) -> str:
    data = [r.to_dict() for r in records]
    return json.dumps(data, indent=indent)


def format_table(records: Sequence[AllowanceRecord], show_zero: bool = False) -> str:
    filtered = records if show_zero else [r for r in records if not r.is_zero]
    if not filtered:
        return "No active token allowances found for this address."

    headers = ["Token", "Symbol", "Spender", "Spender Name", "Allowance", "Balance", "Risk"]
    rows = []
    for r in filtered:
        spender_label = r.spender_label or "Unknown Spender"
        if r.is_unlimited:
            amount_str = "UNLIMITED"
            risk = "CRITICAL" if r.wallet_balance > 0 else "HIGH"
        else:
            amount_str = f"{r.formatted_amount:.4f}".rstrip("0").rstrip(".") if r.formatted_amount else "0"
            risk = "WARN" if r.wallet_balance > 0 and r.raw_amount >= r.wallet_balance else "LOW"

        balance_str = f"{r.formatted_balance:.4f}".rstrip("0").rstrip(".") if r.formatted_balance else "0"

        short_token = f"{r.token_address[:6]}...{r.token_address[-4:]}"
        short_spender = f"{r.spender_address[:6]}...{r.spender_address[-4:]}"

        rows.append([
            short_token,
            (r.token_symbol or "???")[:8],
            short_spender,
            spender_label[:24],
            amount_str,
            balance_str,
            risk,
        ])

    widths = [len(h) for h in headers]
    for row in rows:
        for idx, col in enumerate(row):
            widths[idx] = max(widths[idx], len(col))

    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep_line = "  ".join("-" * widths[i] for i in range(len(headers)))
    body_lines = ["  ".join(col.ljust(widths[i]) for i, col in enumerate(row)) for row in rows]

    summary = f"\nTotal active approvals: {len(filtered)}"
    return "\n".join([header_line, sep_line] + body_lines + [summary])
