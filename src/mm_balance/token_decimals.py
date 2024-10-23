from mm_std import Err, fatal

from mm_balance.config import Config
from mm_balance.constants import NETWORK_APTOS, NETWORK_BITCOIN, NETWORK_SOLANA, Network
from mm_balance.rpc import evm, solana


class TokenDecimals(dict[Network, dict[str | None, int]]):  # {network: {None: 18}} -- None is for native token, ex. ETH
    def __init__(self, networks: list[Network]) -> None:
        super().__init__()
        for network in networks:
            self[network] = {}


def get_token_decimals(config: Config) -> TokenDecimals:
    result = TokenDecimals(config.networks())
    proxies = config.proxies

    for group in config.groups:
        # token_decimals is already known
        if group.token_decimals is not None:
            result[group.network][group.token_address] = group.token_decimals
            continue

        # get token_decimals for known native tokens
        if group.token_address is None:
            if group.network.is_evm_network():
                result[group.network][None] = 18
            elif group.network == NETWORK_SOLANA:
                result[group.network][None] = 9
            elif group.network == NETWORK_BITCOIN:
                result[group.network][None] = 8
            elif group.network == NETWORK_APTOS:
                result[group.network][None] = 8
            else:
                fatal(f"Can't get token decimals for native token on network: {group.network}")
            continue

        # get token_decimals via RPC
        # TODO: group.token_address must be in normalized form, otherwise it can be different for the same token
        if group.token_address in result[group.network]:
            continue  # don't request for a token_decimals twice

        nodes = config.nodes[group.network]
        if group.network.is_evm_network():
            res = evm.get_token_decimals(nodes, group.token_address, proxies)
        elif group.network == NETWORK_SOLANA:
            res = solana.get_token_decimals(nodes, group.token_address, proxies)
        else:
            fatal(f"unsupported network: {group.network}. Cant get token decimals for {group.token_address}")
        if isinstance(res, Err):
            fatal(f"can't get decimals for token {group.ticker} / {group.token_address}, error={res.err}")
        result[group.network][group.token_address] = res.ok

    return result
