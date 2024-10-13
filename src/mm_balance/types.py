from __future__ import annotations

from enum import Enum, unique

DEFAULT_ETH_NODES = ["https://ethereum.publicnode.com", "https://rpc.ankr.com/eth"]
DEFAULT_SOL_NODES = ["https://api.mainnet-beta.solana.com"]


@unique
class Coin(str, Enum):
    BTC = "BTC"
    ETH = "ETH"
    SOL = "SOL"
    USDT = "USDT"
    USDC = "USDC"

    @classmethod
    def usd_coins(cls) -> list[Coin]:
        return [Coin.USDT, Coin.USDC]


@unique
class Network(str, Enum):
    BTC = "btc"
    ETH = "eth"
    SOL = "sol"


@unique
class EthTokenAddress(str, Enum):
    USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
    USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
