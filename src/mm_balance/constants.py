from __future__ import annotations

from enum import Enum, unique

RETRIES_BALANCE = 5
RETRIES_DECIMALS = 5
RETRIES_COINGECKO_PRICES = 5
TIMEOUT_BALANCE = 5
TIMEOUT_DECIMALS = 5


@unique
class Network(str, Enum):
    ARBITRUM_ONE = "arbitrum-one"
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    OP_MAINNET = "op-mainnet"  # Optimism mainnet


TOKEN_ADDRESS: dict[Network, dict[str, str]] = {
    Network.ETHEREUM: {
        "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    },
    Network.SOLANA: {
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    },
    Network.ARBITRUM_ONE: {
        "USDT": "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",
        "USDC": "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8",
    },
    Network.OP_MAINNET: {
        "USDT": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
        "USDC": "0x7f5c764cbc14f9669b88837ca1490cca17c31607",
    },
}

TICKER_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "SOL": "solana",
}

USD_STABLECOINS = ["USDT", "USDC"]

DEFAULT_NODES: dict[Network, list[str]] = {
    Network.ARBITRUM_ONE: ["https://arb1.arbitrum.io/rpc", "https://arbitrum.llamarpc.com"],
    Network.BITCOIN: [],
    Network.ETHEREUM: ["https://ethereum.publicnode.com", "https://rpc.ankr.com/eth"],
    Network.SOLANA: ["https://api.mainnet-beta.solana.com"],
    Network.OP_MAINNET: ["https://mainnet.optimism.io", "https://optimism.llamarpc.com"],
}
