from mm_std import fatal

from mm_balance.config import Config
from mm_balance.constants import NETWORK_APTOS, NETWORK_BITCOIN, NETWORK_SOLANA, Network
from mm_balance.rpc import evm, solana


class TokenDecimals(dict[Network, dict[str | None, int]]):  # {network: {None: 18}} -- None is for native token, ex. ETH
    def __init__(self, networks: list[Network]) -> None:
        super().__init__()
        for network in networks:
            self[network] = {}


async def get_token_decimals(config: Config) -> TokenDecimals:
    result = TokenDecimals(config.networks())
    proxies = config.settings.proxies

    for group in config.groups:
        # token_decimals is already known
        if group.decimals is not None:
            result[group.network][group.token] = group.decimals
            continue

        # get token_decimals for known native tokens
        if group.token is None:
            if group.network.is_evm_network():
                result[group.network][None] = 18
            elif group.network == NETWORK_SOLANA:
                result[group.network][None] = 9
            elif group.network in (NETWORK_BITCOIN, NETWORK_APTOS):
                result[group.network][None] = 8
            else:
                fatal(f"Can't get token decimals for native token on network: {group.network}")
            continue

        # get token_decimals via RPC
        # TODO: group.token_address must be in normalized form, otherwise it can be different for the same token
        if group.token in result[group.network]:
            continue  # don't request for a token_decimals twice

        nodes = config.nodes[group.network]
        if group.network.is_evm_network():
            res = await evm.get_token_decimals(nodes, group.token, proxies)
        elif group.network == NETWORK_SOLANA:
            res = await solana.get_token_decimals(nodes, group.token, proxies)
        else:
            fatal(f"unsupported network: {group.network}. Cant get token decimals for {group.token}")
        if res.is_err():
            fatal(f"can't get decimals for token {group.ticker} / {group.token}, error={res.err}")
        result[group.network][group.token] = res.unwrap()

    return result
