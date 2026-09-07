import asyncio
from typing import Callable, Optional
from token_approval_checker.abi import (
    APPROVAL_TOPIC,
    encode_allowance_call,
    encode_balance_call,
    encode_decimals_call,
    encode_symbol_call,
    decode_uint256,
    decode_string_or_bytes32,
    decode_address_from_topic,
)
from token_approval_checker.known_contracts import get_spender_label
from token_approval_checker.models import AllowanceRecord
from token_approval_checker.rpc import RpcClient

DEFAULT_CHUNK_SIZE = 50000


class Scanner:
    """Scans EVM chains for token approval events and checks current live allowances."""

    def __init__(self, rpc: RpcClient, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.rpc = rpc
        self.chunk_size = chunk_size
        self._token_meta_cache: dict[str, tuple[str, int]] = {}

    async def _fetch_approval_logs(
        self, owner_address: str, from_block: int, to_block: int, progress_cb: Optional[Callable[[int, int], None]] = None
    ) -> list[dict]:
        owner_topic = "0x000000000000000000000000" + owner_address.lower().removeprefix("0x")
        logs = []
        curr = from_block

        while curr <= to_block:
            end = min(curr + self.chunk_size - 1, to_block)
            try:
                chunk_logs = await self.rpc.get_logs(
                    from_block=curr,
                    to_block=end,
                    topics=[APPROVAL_TOPIC, owner_topic],
                )
                logs.extend(chunk_logs)
                if progress_cb:
                    progress_cb(end, to_block)
                curr = end + 1
            except Exception as e:
                # Public RPC providers often choke on large ranges or return 429
                if self.chunk_size > 2000:
                    self.chunk_size = max(1000, self.chunk_size // 4)
                    continue
                raise e

        return logs

    async def _get_metadata(self, token_address: str) -> tuple[str, int]:
        if token_address in self._token_meta_cache:
            return self._token_meta_cache[token_address]

        sym_data = encode_symbol_call()
        dec_data = encode_decimals_call()

        sym_raw, dec_raw = await asyncio.gather(
            self.rpc.eth_call(to=token_address, data=sym_data),
            self.rpc.eth_call(to=token_address, data=dec_data),
            return_exceptions=True,
        )

        symbol = "???"
        if isinstance(sym_raw, str) and sym_raw != "0x":
            symbol = decode_string_or_bytes32(sym_raw) or "???"

        decimals = 18
        if isinstance(dec_raw, str) and dec_raw != "0x":
            parsed = decode_uint256(dec_raw)
            # Some bogus tokens return huge numbers for decimals
            if parsed is not None and 0 <= parsed <= 36:
                decimals = parsed

        self._token_meta_cache[token_address] = (symbol, decimals)
        return symbol, decimals

    # FIXME: scam tokens sometimes emit fake Approval events with victims as owner.
    # Live eth_call checks below filter out most of them because actual allowance is 0.
    async def scan(
        self, owner_address: str, from_block: int = 0, progress_cb: Optional[Callable[[int, int], None]] = None
    ) -> list[AllowanceRecord]:
        latest_block = await self.rpc.get_latest_block_number()
        start_block = max(0, from_block)

        logs = await self._fetch_approval_logs(owner_address, start_block, latest_block, progress_cb)

        # print(f"DEBUG: fetched {len(logs)} logs for {owner_address}")

        pairs: set[tuple[str, str]] = set()
        for log in logs:
            token = log.get("address", "").lower()
            topics = log.get("topics", [])
            if len(topics) >= 3 and token:
                spender = decode_address_from_topic(topics[2])
                if spender:
                    pairs.add((token, spender))

        if not pairs:
            return []

        records: list[AllowanceRecord] = []

        # Check allowances concurrently in batches to avoid overwhelming the endpoint
        pair_list = list(pairs)
        batch_size = 30
        for i in range(0, len(pair_list), batch_size):
            chunk = pair_list[i : i + batch_size]
            allowance_tasks = []
            balance_tasks = []

            for token, spender in chunk:
                allowance_tasks.append(
                    self.rpc.eth_call(to=token, data=encode_allowance_call(owner_address, spender))
                )
                balance_tasks.append(
                    self.rpc.eth_call(to=token, data=encode_balance_call(owner_address))
                )

            allowance_resps = await asyncio.gather(*allowance_tasks, return_exceptions=True)
            balance_resps = await asyncio.gather(*balance_tasks, return_exceptions=True)

            for (token, spender), raw_allw, raw_bal in zip(chunk, allowance_resps, balance_resps):
                if isinstance(raw_allw, Exception) or not isinstance(raw_allw, str):
                    continue

                allowance_val = decode_uint256(raw_allw)
                if allowance_val is None or allowance_val == 0:
                    continue

                balance_val = 0
                if isinstance(raw_bal, str) and not isinstance(raw_bal, Exception):
                    balance_val = decode_uint256(raw_bal) or 0

                symbol, decimals = await self._get_metadata(token)
                records.append(
                    AllowanceRecord(
                        token_address=token,
                        token_symbol=symbol,
                        token_decimals=decimals,
                        spender_address=spender,
                        spender_label=get_spender_label(spender),
                        raw_amount=allowance_val,
                        wallet_balance=balance_val,
                    )
                )

        # Sort unlimited first, then descending by raw amount
        records.sort(key=lambda x: (not x.is_unlimited, -x.raw_amount))
        return records
