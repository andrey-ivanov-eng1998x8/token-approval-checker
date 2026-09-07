from typing import Optional

APPROVAL_EVENT_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
ALLOWANCE_SELECTOR = "0xdd62ed3e"  # allowance(address,address)
DECIMALS_SELECTOR = "0x313ce567"   # decimals()
SYMBOL_SELECTOR = "0x95d89b41"     # symbol()
NAME_SELECTOR = "0x06fdde03"       # name()


def _rotl64(x: int, n: int) -> int:
    return ((x << n) & 0xFFFFFFFFFFFFFFFF) | (x >> (64 - n))


RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

RHO = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]


def keccak256(data: bytes) -> bytes:
    """Pure Python Keccak-256 (EVM variant, not FIPS SHA3)."""
    rate = 136
    state = [[0] * 5 for _ in range(5)]

    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != 0:
        padded.append(0x00)
    padded[-1] |= 0x80

    for block_start in range(0, len(padded), rate):
        block = padded[block_start : block_start + rate]
        for i in range(17):
            val = int.from_bytes(block[i * 8 : (i + 1) * 8], "little")
            state[i % 5][i // 5] ^= val

        for round_idx in range(24):
            c = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
            d = [c[(x + 4) % 5] ^ _rotl64(c[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    state[x][y] ^= d[x]

            b = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    b[y][(2 * x + 3 * y) % 5] = _rotl64(state[x][y], RHO[x][y])

            for x in range(5):
                for y in range(5):
                    state[x][y] = b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y])

            state[0][0] ^= RC[round_idx]

    out = bytearray()
    for i in range(4):
        out.extend(state[i % 5][i // 5].to_bytes(8, "little"))
    return bytes(out)


def pad_to_word(val: str) -> str:
    return val.rjust(64, "0")


def encode_address(address: str) -> str:
    clean = address.lower().replace("0x", "")
    if len(clean) != 40:
        raise ValueError(f"Invalid address length: {address}")
    return pad_to_word(clean)


def decode_address_topic(topic: str) -> str:
    clean = topic.replace("0x", "")
    if len(clean) < 40:
        return "0x" + clean.zfill(40)
    # The last 40 hex characters represent the address
    return "0x" + clean[-40:].lower()


def encode_allowance_call(owner: str, spender: str) -> str:
    # TODO(perf): selector string can be pre-computed constant instead of string join
    return ALLOWANCE_SELECTOR + encode_address(owner) + encode_address(spender)


def decode_uint256(hex_str: Optional[str]) -> int:
    if not hex_str or hex_str == "0x":
        return 0
    clean = hex_str.replace("0x", "")
    return int(clean, 16)


def decode_string_or_bytes32(raw_hex: Optional[str]) -> str:
    if not raw_hex or raw_hex == "0x":
        return ""
    raw = bytes.fromhex(raw_hex.replace("0x", ""))
    if len(raw) < 32:
        return ""

    # Check if this is standard dynamic ABI string (offset -> length -> data)
    if len(raw) >= 64:
        offset = int.from_bytes(raw[0:32], "big")
        if offset == 32 and len(raw) >= 64:
            length = int.from_bytes(raw[32:64], "big")
            content = raw[64 : 64 + length]
            return content.decode("utf-8", errors="ignore").strip("\x00")

    # Fallback for old tokens (e.g. MKR) returning plain bytes32
    return raw.decode("utf-8", errors="ignore").strip("\x00 ")
