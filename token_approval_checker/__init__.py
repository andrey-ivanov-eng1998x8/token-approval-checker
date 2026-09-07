"""Lightweight ERC-20 allowance checker without web3.py overhead."""

from token_approval_checker.scanner import AllowanceScanner
from token_approval_checker.models import AllowanceRecord

__version__ = "0.2.0"
__all__ = ["AllowanceScanner", "AllowanceRecord", "__version__"]
