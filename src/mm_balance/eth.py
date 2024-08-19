from decimal import Decimal

from eth_utils.conversions import to_int
from mm_eth import abi, erc20, rpc
from mm_std import Err, Ok, Result

from mm_balance.config import Config
from mm_balance.types import EthTokenAddress, Network


def get_balance(address: str, token_address: str | None, config: Config) -> Result[Decimal]:
    if token_address is not None and token_address.lower() == EthTokenAddress.SDAI:
        return _get_sdai_balance(config.nodes[Network.ETH], address, config.proxies, config.round_ndigits, attempts=5)
    if token_address is not None:
        return erc20.get_balance(
            config.nodes[Network.ETH],
            token_address,
            address,
            proxies=config.proxies,
            attempts=5,
            timeout=10,
        ).and_then(
            lambda b: Ok(round(Decimal(b / 10 ** config.token_decimals.eth[token_address]), config.round_ndigits)),
        )
    else:
        return rpc.eth_get_balance(config.nodes[Network.ETH], address, proxies=config.proxies, attempts=5, timeout=10).and_then(
            lambda b: Ok(round(Decimal(b / 10**18), config.round_ndigits)),
        )


def get_token_decimals(token_address: str, config: Config) -> Result[int]:
    return erc20.get_decimals(config.nodes[Network.ETH], token_address, timeout=10, proxies=config.proxies, attempts=5)


def _get_sdai_balance(nodes: list[str], address: str, proxies: list[str], round_ndigits: int, attempts: int) -> Result[Decimal]:
    data = abi.encode_function_input_by_signature("maxWithdraw(address)", [address])
    res = rpc.eth_call(nodes, EthTokenAddress.SDAI, data, proxies=proxies, attempts=attempts)
    if isinstance(res, Err):
        return res
    balance = to_int(hexstr=res.ok)
    return Ok(Decimal(str(round(balance / 10**18, ndigits=round_ndigits))))
