from decimal import Decimal

from mm_apt import retry as apt_retry
from mm_btc.blockstream import BlockstreamClient
from mm_crypto_utils import Nodes, Proxies
from mm_eth import retry as eth_retry
from mm_sol import retry as sol_retry
from mm_std import Result

from mm_balance.constants import (
    NETWORK_APTOS,
    NETWORK_BITCOIN,
    NETWORK_SOLANA,
    RETRIES_BALANCE,
    RETRIES_DECIMALS,
    TIMEOUT_BALANCE,
    TIMEOUT_DECIMALS,
    Network,
)
from mm_balance.utils import scale_and_round


async def get_balance(
    *,
    network: Network,
    nodes: Nodes,
    proxies: Proxies,
    wallet_address: str,
    token_address: str | None,
    token_decimals: int,
    ndigits: int,
) -> Result[Decimal]:
    if network.is_evm_network():
        if token_address is None:
            res = await eth_retry.eth_get_balance(
                RETRIES_BALANCE, nodes, proxies, address=wallet_address, timeout=TIMEOUT_BALANCE
            )
        else:
            res = await eth_retry.erc20_balance(
                RETRIES_BALANCE, nodes, proxies, token=token_address, wallet=wallet_address, timeout=TIMEOUT_BALANCE
            )
    elif network == NETWORK_BITCOIN:
        res = await BlockstreamClient(proxies=proxies, attempts=RETRIES_BALANCE).get_confirmed_balance(wallet_address)
    elif network == NETWORK_APTOS:
        if token_address is None:
            token_address = "0x1::aptos_coin::AptosCoin"  # noqa: S105 # nosec
        res = await apt_retry.get_balance(
            RETRIES_BALANCE, nodes, proxies, account=wallet_address, coin_type=token_address, timeout=TIMEOUT_BALANCE
        )
    elif network == NETWORK_SOLANA:
        if token_address is None:
            res = await sol_retry.get_sol_balance(
                RETRIES_BALANCE, nodes, proxies, address=wallet_address, timeout=TIMEOUT_BALANCE
            )
        else:
            res = await sol_retry.get_token_balance(
                RETRIES_BALANCE, nodes, proxies, owner=wallet_address, token=token_address, timeout=TIMEOUT_BALANCE
            )
    else:
        return Result.err("Unsupported network")
    return res.map(lambda value: scale_and_round(value, token_decimals, ndigits))


async def get_token_decimals(
    *,
    network: Network,
    nodes: Nodes,
    proxies: Proxies,
    token_address: str,
) -> Result[int]:
    if network.is_evm_network():
        return await eth_retry.erc20_decimals(RETRIES_DECIMALS, nodes, proxies, token=token_address, timeout=TIMEOUT_DECIMALS)
    if network == NETWORK_SOLANA:
        return await sol_retry.get_token_decimals(RETRIES_DECIMALS, nodes, proxies, token=token_address, timeout=TIMEOUT_DECIMALS)
    return Result.err("Unsupported network")
