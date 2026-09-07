import argparse
import sys
from token_approval_checker.scanner import scan_wallet
from token_approval_checker.formatters import format_table, format_json

# Quick chain aliases to avoid typing long public urls every time
CHAIN_PRESETS = {
    "mainnet": "https://eth.llamarpc.com",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "optimism": "https://mainnet.optimism.io",
    "polygon": "https://polygon-rpc.com",
    "base": "https://mainnet.base.org",
    "bsc": "https://binance.llamarpc.com",
}


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
        default=None,
        help="custom JSON-RPC endpoint URL",
    )
    p.add_argument(
        "--chain",
        "-c",
        choices=list(CHAIN_PRESETS.keys()),
        default="mainnet",
        help="target chain preset if custom rpc is omitted (default: mainnet)",
    )
    p.add_argument(
        "--block-depth",
        "-b",
        type=int,
        default=100000,
        help="how many past blocks to scan Approval logs for (default: 100000)",
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
    p.add_argument(
        "--show-zero",
        action="store_true",
        help="include historical approvals that were later wiped to 0",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="rpc request timeout in seconds (default: 15)",
    )
    return p.parse_args(args)


def main(args=None) -> int:
    """CLI entry point for running wallet allowance audits."""
    opts = parse_args(args)

    target = opts.wallet.strip()
    if not is_valid_address(target):
        sys.stderr.write(f"error: '{target}' is not a valid 20-byte hex address\n")
        return 1

    rpc_endpoint = opts.rpc or CHAIN_PRESETS[opts.chain]

    # TODO: add support for reading addresses from stdin for batch pipeline runs
    # print(f"DEBUG: resolved rpc url = {rpc_endpoint}")

    try:
        approvals = scan_wallet(
            wallet_address=target,
            rpc_url=rpc_endpoint,
            block_depth=opts.block_depth,
            unlimited_only=opts.unlimited_only,
            include_zero=opts.show_zero,
            timeout=opts.timeout,
        )
    except KeyboardInterrupt:
        sys.stderr.write("\naborted by user\n")
        return 130
    except Exception as exc:
        sys.stderr.write(f"scan failed: {exc}\n")
        return 2

    if opts.json:
        print(format_json(approvals))
    else:
        print(format_table(approvals, target, chain_name=opts.chain if not opts.rpc else "custom"))

    return 0
