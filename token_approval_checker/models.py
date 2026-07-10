from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class TokenInfo:
    address: str
    symbol: str
    name: str
    decimals: int


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

    @property
    def is_unlimited(self) -> bool:
        # 2^255 or higher is practically infinite (uint256 max is 2^256 - 1)
        return self.amount >= (1 << 255)

    @property
    def formatted_amount(self) -> str:
        if self.is_unlimited:
            return "UNLIMITED"
        if self.amount == 0:
            return "0"
        
        val = Decimal(self.amount) / Decimal(10 ** self.token.decimals)
        s = f"{val:.6f}".rstrip("0").rstrip(".")
        return s if s else "0"
