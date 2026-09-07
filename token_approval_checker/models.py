from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

# Anything above 2^128 is treated as infinite in practice
UNLIMITED_THRESHOLD = 2**128


@dataclass(frozen=True)
class TokenInfo:
    address: str
    symbol: str
    name: str
    decimals: int = 18


@dataclass
class SpenderInfo:
    address: str
    label: Optional[str] = None
    protocol: Optional[str] = None
    verified: bool = False


@dataclass
class ApprovalRecord:
    wallet_address: str
    token: TokenInfo
    spender: SpenderInfo
    amount: int
    block_number: Optional[int] = None

    @property
    def is_unlimited(self) -> bool:
        # uint256 max is 2^256 - 1, but many dapps approve 2^128 or 10^36
        return self.amount >= UNLIMITED_THRESHOLD

    @property
    def formatted_amount(self) -> str:
        if self.is_unlimited:
            return "UNLIMITED"
        if self.amount == 0:
            return "0"
        
        # some weird tokens like GEM have 0 decimals or invalid metadata
        decimals = max(0, self.token.decimals)
        val = Decimal(self.amount) / Decimal(10 ** decimals)
        # print(f"dbg: {self.token.symbol} {self.amount} -> {val}")
        s = f"{val:.6f}".rstrip("0").rstrip(".")
        return s if s else "0"

    @property
    def risk_level(self) -> str:
        # FIXME: flag unverified contracts even when allowance is finite but large
        if not self.spender.verified and self.is_unlimited:
            return "HIGH"
        if self.is_unlimited:
            return "MEDIUM"
        return "LOW"
