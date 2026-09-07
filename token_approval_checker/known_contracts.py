from typing import Optional
from token_approval_checker.models import SpenderInfo

# Spenders mapped by chain_id -> address (lowercase) -> (label, protocol)
KNOWN_SPENDERS: dict[int, dict[str, tuple[str, str]]] = {
    # Ethereum Mainnet
    1: {
        "0x000000000022d473030f116ddee9f6b43ac78ba3": ("Permit2", "Uniswap"),
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": ("SwapRouter02", "Uniswap"),
        "0xe592427a0aece92de3edee1f18e0157c05861564": ("SwapRouter", "Uniswap v3"),
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": ("Router02", "Uniswap v2"),
        "0x1111111254eeb25477b68fb85ed929f73a960582": ("AggregationRouterV5", "1inch"),
        "0x111111125421ca6dc452d289314280a0f8842a65": ("AggregationRouterV6", "1inch"),
        "0xdef1c7ced8d7de3306579a361fa303493130f7f2": ("ExchangeProxy", "0x Project"),
        "0x00000000000000adc04c56bf30ac9d3c0aaf14dc": ("Seaport 1.5", "OpenSea"),
        "0x0000000000000068f116a894984e2db1123eb395": ("Seaport 1.6", "OpenSea"),
        "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": ("SushiSwap Router", "Sushi"),
        "0x881d40237659add45182e337dc5e3474554393b8": ("Metamask Swap Router", "MetaMask"),
        "0x3a23f943181408eac424116af7b7790c94cb97a5": ("Bridge", "Socket / Bungee"),
        "0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae": ("LiFi Diamond", "LI.FI"),
    },
    # Arbitrum One
    42161: {
        "0x000000000022d473030f116ddee9f6b43ac78ba3": ("Permit2", "Uniswap"),
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": ("SwapRouter02", "Uniswap"),
        "0xe592427a0aece92de3edee1f18e0157c05861564": ("SwapRouter", "Uniswap v3"),
        "0x111111125421ca6dc452d289314280a0f8842a65": ("AggregationRouterV6", "1inch"),
        "0xdef1c7ced8d7de3306579a361fa303493130f7f2": ("ExchangeProxy", "0x Project"),
        "0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae": ("LiFi Diamond", "LI.FI"),
        "0xaabb32997e3a35b84c8a2ef867fb7492c7fae94e": ("Camelot Router", "Camelot"),
    },
    # Optimism
    10: {
        "0x000000000022d473030f116ddee9f6b43ac78ba3": ("Permit2", "Uniswap"),
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": ("SwapRouter02", "Uniswap"),
        "0x111111125421ca6dc452d289314280a0f8842a65": ("AggregationRouterV6", "1inch"),
        "0xdef1c7ced8d7de3306579a361fa303493130f7f2": ("ExchangeProxy", "0x Project"),
    },
    # Base
    8453: {
        "0x000000000022d473030f116ddee9f6b43ac78ba3": ("Permit2", "Uniswap"),
        "0x2626664c2603336e57b271c5c0b26f421741e481": ("SwapRouter02", "Uniswap"),
        "0x111111125421ca6dc452d289314280a0f8842a65": ("AggregationRouterV6", "1inch"),
        "0xdef1c7ced8d7de3306579a361fa303493130f7f2": ("ExchangeProxy", "0x Project"),
        "0x327df1e6de05895d2ab08513aadd9313fe505d86": ("Aerodrome Router", "Aerodrome"),
    },
    # Polygon
    137: {
        "0x000000000022d473030f116ddee9f6b43ac78ba3": ("Permit2", "Uniswap"),
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": ("SwapRouter02", "Uniswap"),
        "0x111111125421ca6dc452d289314280a0f8842a65": ("AggregationRouterV6", "1inch"),
        "0xdef1c7ced8d7de3306579a361fa303493130f7f2": ("ExchangeProxy", "0x Project"),
        "0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff": ("QuickSwap Router", "QuickSwap"),
    },
}


def get_known_spender(address: str, chain_id: int = 1) -> Optional[SpenderInfo]:
    key = address.lower()
    chain_table = KNOWN_SPENDERS.get(chain_id, {})
    
    if key in chain_table:
        label, protocol = chain_table[key]
        return SpenderInfo(address=address, label=label, protocol=protocol, verified=True)
    
    # fallback to mainnet table if not found in specific chain (many deploy deterministic addresses)
    if chain_id != 1 and key in KNOWN_SPENDERS[1]:
        label, protocol = KNOWN_SPENDERS[1][key]
        return SpenderInfo(address=address, label=label, protocol=protocol, verified=True)

    return None
