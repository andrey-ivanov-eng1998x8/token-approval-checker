from token_approval_checker.scanner import ApprovalScanner
from token_approval_checker.abi import APPROVAL_TOPIC, pad_address, encode_call


class FakeRpcClient:
    def __init__(self, logs_by_range=None, allowances=None, metadata=None):
        self.logs_by_range = logs_by_range or {}
        self.allowances = allowances or {}
        self.metadata = metadata or {}
        self.call_history = []

    def get_logs(self, params):
        from_b = params.get("fromBlock")
        to_b = params.get("toBlock")
        return self.logs_by_range.get((from_b, to_b), [])

    def eth_call(self, to_addr, data):
        self.call_history.append((to_addr, data))
        if data.startswith("0xdd62ed3e"):
            key = (to_addr.lower(), data.lower())
            return self.allowances.get(key, "0x" + "0" * 64)
        if data.startswith("0x95d89b41"):  # symbol()
            return self.metadata.get((to_addr.lower(), "symbol"), "0x")
        if data.startswith("0x313ce567"):  # decimals()
            return self.metadata.get((to_addr.lower(), "decimals"), "0x12")
        return "0x"

    def get_block_number(self):
        return 18000000


def test_scanner_chunked_block_ranges():
    owner = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    spender = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
    token = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

    # range 100-199 has no events, range 200-250 has one
    log_event = {
        "address": token,
        "topics": [
            APPROVAL_TOPIC,
            "0x" + pad_address(owner),
            "0x" + pad_address(spender),
        ],
        "data": "0x0000000000000000000000000000000000000000000000000000000000000064",
        "blockNumber": "0xd0",
        "transactionHash": "0xfeedface",
    }

    logs_by_range = {
        (100, 199): [],
        (200, 250): [log_event],
    }

    call_data = encode_call("allowance(address,address)", owner, spender).lower()
    allowances = {
        (token.lower(), call_data): "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000",  # 1 DAI
    }

    rpc = FakeRpcClient(logs_by_range=logs_by_range, allowances=allowances)
    scanner = ApprovalScanner(rpc, block_chunk_size=100)
    results = scanner.scan(owner, from_block=100, to_block=250)

    # print(results)  # left for manual inspection if needed
    assert len(results) == 1
    assert results[0].raw_allowance == 1000000000000000000
    assert not results[0].is_unlimited


def test_scanner_handles_missing_token_symbol():
    owner = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    spender = "0xdef1c0ded9bec7f1a1670819833240f027b25eff"
    token = "0x111111111117dC0aa78b770fA6A738034120C302"

    log_event = {
        "address": token,
        "topics": [
            APPROVAL_TOPIC,
            "0x" + pad_address(owner),
            "0x" + pad_address(spender),
        ],
        "data": "0x" + "f" * 64,
        "blockNumber": "0x1234",
        "transactionHash": "0xcafe",
    }

    call_data = encode_call("allowance(address,address)", owner, spender).lower()
    allowances = {
        (token.lower(), call_data): "0x" + "f" * 64,
    }

    # Symbol call returns empty / failure; decimals defaults or fails
    metadata = {
        (token.lower(), "symbol"): "0x",
        (token.lower(), "decimals"): "0x",
    }

    rpc = FakeRpcClient(logs_by_range={(0, 100): [log_event]}, allowances=allowances, metadata=metadata)
    scanner = ApprovalScanner(rpc, block_chunk_size=100)
    results = scanner.scan(owner, from_block=0, to_block=100)

    assert len(results) == 1
    assert results[0].token_symbol == "UNKNOWN" or results[0].token_symbol == "???"
    assert results[0].is_unlimited
