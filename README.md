# token-approval-checker

A small CLI to check ERC-20 token approvals and unlimited allowances on EVM addresses.
I wrote this because pulling in web3.py just to encode two ABI calls and hit `eth_call` was overkill for quick audits.

## Install

```bash
pip install .
```

Or run directly with `pipx`:

```bash
pipx run .
```

## Usage

Scan an address on Ethereum mainnet:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

Use a custom RPC endpoint:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --rpc https://eth.llamarpc.com
```

Filter only infinite / unbounded approvals:

```bash
tac 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --only-infinite
```
