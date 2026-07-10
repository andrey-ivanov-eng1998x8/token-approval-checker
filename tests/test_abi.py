import pytest
from token_approval_checker.abi import (
    keccak256,
    function_selector,
    encode_call,
    decode_uint256,
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


