import pytest
from token_approval_checker.abi import (
    keccak256,
    function_selector,
    encode_call,
    decode_uint256,
    decode_string,
    pad_address,
    topic_to_address,
    APPROVAL_TOPIC,
)


def test_keccak256_empty():
    # standard keccak-256 hash of empty byte sequence
    expected = "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    assert keccak256(b"").hex() == expected


def test_function_selector():
    assert function_selector("allowance(address,address)") == "dd62ed3e"
    assert function_selector("balanceOf(address)") == "70a08231"
    assert function_selector("symbol()") == "95d89b41"
    assert function_selector("decimals()") == "313ce567"


def test_approval_topic():
    expected = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
    assert APPROVAL_TOPIC == expected


def test_pad_address():
    raw = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    padded = pad_address(raw)
    assert len(padded) == 64
    assert padded.startswith("000000000000000000000000")
    assert padded.lower().endswith(raw[2:].lower())


def test_pad_address_invalid():
    with pytest.raises(ValueError):
        pad_address("0x123")


def test_topic_to_address():
    topic = "0x000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa96045"
    assert topic_to_address(topic) == "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"


def test_encode_call_allowance():
    owner = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    spender = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    encoded = encode_call("allowance(address,address)", owner, spender)
    assert encoded.startswith("0xdd62ed3e")
    # 4 bytes selector + 32 bytes owner + 32 bytes spender = 68 bytes = 136 hex chars + 0x prefix
    assert len(encoded) == 2 + 8 + 64 + 64


def test_decode_uint256():
    assert decode_uint256("0x0") == 0
    assert decode_uint256("0x00") == 0
    assert decode_uint256("0x0f") == 15
    max_uint256_hex = "0x" + "f" * 64
    assert decode_uint256(max_uint256_hex) == (1 << 256) - 1


def test_decode_uint256_invalid():
    with pytest.raises(ValueError):
        decode_uint256("invalid_hex")


def test_decode_string_abi_format():
    # ABI encoded "USDC" string: offset 0x20, length 4, utf8 bytes + padding
    offset = "0000000000000000000000000000000000000000000000000000000000000020"
    length = "0000000000000000000000000000000000000000000000000000000000000004"
    data = "5553444300000000000000000000000000000000000000000000000000000000"
    raw_hex = f"0x{offset}{length}{data}"
    assert decode_string(raw_hex) == "USDC"


def test_decode_string_bytes32_fallback():
    # Some older tokens (like MKR) returned bytes32 instead of string for symbol()
    # "MKR" followed by zeroes in a single 32-byte word
    mkr_hex = "0x4d4b520000000000000000000000000000000000000000000000000000000000"
    assert decode_string(mkr_hex) == "MKR"
