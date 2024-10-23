from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

RETRIES_BALANCE = 5
RETRIES_DECIMALS = 5
RETRIES_COINGECKO_PRICES = 5
TIMEOUT_BALANCE = 5
TIMEOUT_DECIMALS = 5


class Network(str):
    def is_evm_network(self) -> bool:
        return self in [NETWORK_ETHEREUM, NETWORK_ARBITRUM_ONE, NETWORK_OP_MAINNET] or self.startswith("evm-")

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


NETWORK_APTOS = Network("aptos")
NETWORK_ARBITRUM_ONE = Network("arbitrum-one")
NETWORK_BITCOIN = Network("bitcoin")
NETWORK_ETHEREUM = Network("ethereum")
NETWORK_SOLANA = Network("solana")
NETWORK_OP_MAINNET = Network("op-mainnet")
NETWORKS = [NETWORK_APTOS, NETWORK_ARBITRUM_ONE, NETWORK_BITCOIN, NETWORK_ETHEREUM, NETWORK_SOLANA, NETWORK_OP_MAINNET]


TOKEN_ADDRESS: dict[Network, dict[str, str]] = {
    NETWORK_ETHEREUM: {
        "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    },
    NETWORK_SOLANA: {
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    },
    NETWORK_ARBITRUM_ONE: {
        "USDT": "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",
        "USDC": "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8",
    },
    NETWORK_OP_MAINNET: {
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
    "APT": "aptos",
    "POL": "matic-network",
}

USD_STABLECOINS = ["USDT", "USDC"]

DEFAULT_NODES: dict[Network, list[str]] = {
    NETWORK_ARBITRUM_ONE: ["https://arb1.arbitrum.io/rpc", "https://arbitrum.llamarpc.com"],
    NETWORK_BITCOIN: [],
    NETWORK_ETHEREUM: ["https://ethereum.publicnode.com", "https://rpc.ankr.com/eth"],
    NETWORK_SOLANA: ["https://api.mainnet-beta.solana.com"],
    NETWORK_OP_MAINNET: ["https://mainnet.optimism.io", "https://optimism.llamarpc.com"],
    NETWORK_APTOS: ["https://fullnode.mainnet.aptoslabs.com/v1"],
}
