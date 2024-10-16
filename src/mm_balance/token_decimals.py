from mm_std import Err, fatal

from mm_balance.config import Config
from mm_balance.constants import Network
from mm_balance.rpc import eth, solana


class TokenDecimals(dict[Network, dict[str, int]]):
    def __init__(self) -> None:
        super().__init__()
        for network in Network:
            self[network] = {}


def get_token_decimals(config: Config) -> TokenDecimals:
    result = TokenDecimals()

    for group in config.groups:
        if group.token_address is None or group.token_address in result[group.network]:
            continue

        nodes = config.nodes[group.network]
        proxies = config.proxies

        match group.network:
            case Network.ETHEREUM:
                decimals_res = eth.get_token_decimals(nodes, group.token_address, proxies)
            case Network.SOLANA:
                decimals_res = solana.get_token_decimals(nodes, group.token_address, proxies)
            case _:
                raise ValueError(f"unsupported network: {group.network}. Cant get token decimals for {group.token_address}")

        if isinstance(decimals_res, Err):
            fatal(f"can't get decimals for token {group.ticker} / {group.token_address}, error={decimals_res.err}")
        result[group.network][group.token_address] = decimals_res.ok

    return result
