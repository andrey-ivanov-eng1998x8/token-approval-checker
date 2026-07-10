import argparse
import sys
from token_approval_checker.scanner import scan_wallet
from token_approval_checker.formatters import format_table, format_json


def is_valid_address(addr: str) -> bool:
    if not addr.startswith("0x") or len(addr) != 42:
        return False
    try:
        int(addr[2:], 16)
        return True
    except ValueError:
        return False


def parse_args(args=None):
    p = argparse.ArgumentParser(
        prog="token-approval-checker",
        description="Inspect ERC-20 allowances and infinite spend approvals for an EVM wallet.",
    )
    p.add_argument("wallet", help="target wallet address (0x...)")
    p.add_argument(
        "--rpc",
        "-r",
        default="https://eth.llamarpc.com",
        help="JSON-RPC endpoint URL (defaults to llamarpc)",
    )
    p.add_argument(
        "--block-depth",
        "-b",
        type=int,
        default=100000,
        help="how many past blocks to scan Approval logs for (default 100k)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="output results in json format",
    )
    p.add_argument(
        "--unlimited-only",
        action="store_true",
        help="only list allowances exceeding standard safe limits",
    )
    return p.parse_args(args)


def main(args=None) -> int:
    opts = parse_args(args)

    target = opts.wallet.strip()
    if not is_valid_address(target):
        sys.stderr.write(f"error: '{target}' is not a valid 20-byte hex address\n")
        return 1

    # print(f"DEBUG: scanning {target} on {opts.rpc}")
    try:
        approvals = scan_wallet(
            wallet_address=target,
            rpc_url=opts.rpc,
            block_depth=opts.block_depth,
            unlimited_only=opts.unlimited_only,
        )
    except Exception as exc:
        sys.stderr.write(f"scan failed: {exc}\n")
        return 2

    if opts.json:
        print(format_json(approvals))
    else:
        print(format_table(approvals, target))

    return 0
