import math
from typing import Any, List, Union

# Standard ERC-20 approval event and function selectors
# approval(address,address,uint256) signature hash
APPROVAL_EVENT_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
ALLOWANCE_SELECTOR = "0xdd62ed3e"  # allowance(address,address)
DECIMALS_SELECTOR = "0x313ce567"   # decimals()
SYMBOL_SELECTOR = "0x95d89b41"     # symbol()
NAME_SELECTOR = "0x06fdde03"       # name()


def _rotl64(x: int, n: int) -> int:
    return ((x << n) & 0xFFFFFFFFFFFFFFFF) | (x >> (64 - n))


# Round constants for keccak-f[1600]
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
    # 1088 bits = 136 bytes rate for 256-bit capacity
    rate = 136
    state = [[0] * 5 for _ in range(5)]

    # Pad input with 0x01 ... 0x80 (standard keccak padding)
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

        # 24 rounds of keccak-f[1600]
        for round_idx in range(24):
            # Theta
            c = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
            d = [c[(x + 4) % 5] ^ _rotl64(c[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    state[x][y] ^= d[x]

            # Rho and Pi
            b = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    b[y][(2 * x + 3 * y) % 5] = _rotl64(state[x][y], RHO[x][y])

            # Chi
            for x in range(5):
                for y in range(5):
                    state[x][y] = b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y])

            # Iota
            state[0][0] ^= RC[round_idx]

    out = bytearray()
    for i in range(4):
        out.extend(state[i % 5][i // 5].to_bytes(8, "little"))
    return bytes(out)


def encode_address(address: str) -> str:
    clean = address.lower().replace("0x", "")
    if len(clean) != 40:
        raise ValueError(f"Invalid address length: {address}")
    return clean.rjust(64, "0")


def encode_allowance_call(owner: str, spender: str) -> str:
    return ALLOWANCE_SELECTOR + encode_address(owner) + encode_address(spender)


def decode_uint256(hex_str: str) -> int:
    if not hex_str or hex_str == "0x":
        return 0
    clean = hex_str.replace("0x", "")
    return int(clean, 16)
