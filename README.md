# token-approval-checker

A small CLI to check ERC-20 token approvals and unlimited allowances on EVM addresses.
I wrote this because pulling in web3.py just to encode two ABI calls and hit `eth_call` was overkill for quick audits.

It queries standard ERC-20 contracts directly using lightweight JSON-RPC over HTTP, decodes decimals and spender names against a local list of known routers/protocols, and flags dangerous unlimited approvals.

## Install

```bash
pip install .
```

Or install in editable mode for dev:

```bash
pip install -e ".[dev]"
```

## Usage

Scan an address on Ethereum mainnet:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

Target another chain:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --chain arbitrum
```

Available built-in network aliases: `ethereum`, `arbitrum`, `optimism`, `polygon`, `base`, `bsc`.

Or supply any custom RPC URL:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --rpc https://arb1.arbitrum.io/rpc
```

Filter to show only infinite (uint256 max or near-max) allowances:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --only-infinite
```

Output raw JSON (useful for piping into `jq` or alerting scripts):

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --json
```

Supply a custom list of token addresses:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --tokens tokens.txt
```

Adjust concurrency if public RPCs rate limit you:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --concurrency 3 --delay 0.1
```

<!-- refreshed: 2026-09-17 -->
