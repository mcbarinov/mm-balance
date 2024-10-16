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
    # TODO: Add for Arbitrum and Optimism, usdt + usdc
}

TICKER_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "SOL": "solana",
}

USD_STABLECOINS = ["USDT", "USDC"]

DEFAULT_ETHEREUM_NODES = ["https://ethereum.publicnode.com", "https://rpc.ankr.com/eth"]
DEFAULT_SOLANA_NODES = ["https://api.mainnet-beta.solana.com"]
DEFAULT_ARBITRUM_ONE_NODES = ["https://arb1.arbitrum.io/rpc", "https://arbitrum.llamarpc.com"]
DEFAULT_OP_MAINNET_NODES = ["https://mainnet.optimism.io", "https://optimism.llamarpc.com"]
