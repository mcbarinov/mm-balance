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
    """
    Fetch balance for a wallet on specified network.

    This function retrieves the balance of a wallet address on a given network.
    It supports multiple networks including EVM-compatible chains (Ethereum,
    Arbitrum, etc.), Bitcoin, Aptos, and Solana. For EVM networks and Solana,
    it can fetch both native coin and token balances.

    Args:
        network: The blockchain network to query
        nodes: RPC nodes to use for the request
        proxies: Proxy configuration for the request
        wallet_address: The address of the wallet to check
        token_address: The address of the token (None for native coin)
        token_decimals: Number of decimal places for the token
        ndigits: Number of digits to round the result to

    Returns:
        Result containing the balance as a Decimal on success, or an error message
    """
    if network.is_evm_network():
        return await _get_evm_balance(
            nodes=nodes,
            proxies=proxies,
            wallet_address=wallet_address,
            token_address=token_address,
            token_decimals=token_decimals,
            ndigits=ndigits,
        )
    if network == NETWORK_BITCOIN:
        return await _get_bitcoin_balance(
            proxies=proxies,
            wallet_address=wallet_address,
            token_decimals=token_decimals,
            ndigits=ndigits,
        )
    if network == NETWORK_APTOS:
        return await _get_aptos_balance(
            nodes=nodes,
            proxies=proxies,
            wallet_address=wallet_address,
            token_address=token_address,
            token_decimals=token_decimals,
            ndigits=ndigits,
        )
    if network == NETWORK_SOLANA:
        return await _get_solana_balance(
            nodes=nodes,
            proxies=proxies,
            wallet_address=wallet_address,
            token_address=token_address,
            token_decimals=token_decimals,
            ndigits=ndigits,
        )
    return Result.err("Unsupported network")


async def _get_evm_balance(
    *,
    nodes: Nodes,
    proxies: Proxies,
    wallet_address: str,
    token_address: str | None,
    token_decimals: int,
    ndigits: int,
) -> Result[Decimal]:
    """Fetch balance for EVM-compatible networks."""
    if token_address is None:
        res = await eth_retry.eth_get_balance(RETRIES_BALANCE, nodes, proxies, address=wallet_address, timeout=TIMEOUT_BALANCE)
    else:
        res = await eth_retry.erc20_balance(
            RETRIES_BALANCE, nodes, proxies, token=token_address, wallet=wallet_address, timeout=TIMEOUT_BALANCE
        )
    return res.map(lambda value: scale_and_round(value, token_decimals, ndigits))


async def _get_bitcoin_balance(
    *,
    proxies: Proxies,
    wallet_address: str,
    token_decimals: int,
    ndigits: int,
) -> Result[Decimal]:
    """Fetch balance for Bitcoin network."""
    res = await BlockstreamClient(proxies=proxies, attempts=RETRIES_BALANCE).get_confirmed_balance(wallet_address)
    return res.map(lambda value: scale_and_round(value, token_decimals, ndigits))


async def _get_aptos_balance(
    *,
    nodes: Nodes,
    proxies: Proxies,
    wallet_address: str,
    token_address: str | None,
    token_decimals: int,
    ndigits: int,
) -> Result[Decimal]:
    """Fetch balance for Aptos network."""
    actual_token_address = token_address if token_address is not None else "0x1::aptos_coin::AptosCoin"
    res = await apt_retry.get_balance(
        RETRIES_BALANCE, nodes, proxies, account=wallet_address, coin_type=actual_token_address, timeout=TIMEOUT_BALANCE
    )
    return res.map(lambda value: scale_and_round(value, token_decimals, ndigits))


async def _get_solana_balance(
    *,
    nodes: Nodes,
    proxies: Proxies,
    wallet_address: str,
    token_address: str | None,
    token_decimals: int,
    ndigits: int,
) -> Result[Decimal]:
    """Fetch balance for Solana network."""
    if token_address is None:
        res = await sol_retry.get_sol_balance(RETRIES_BALANCE, nodes, proxies, address=wallet_address, timeout=TIMEOUT_BALANCE)
    else:
        res = await sol_retry.get_token_balance(
            RETRIES_BALANCE, nodes, proxies, owner=wallet_address, token=token_address, timeout=TIMEOUT_BALANCE
        )
    return res.map(lambda value: scale_and_round(value, token_decimals, ndigits))


async def get_token_decimals(
    *,
    network: Network,
    nodes: Nodes,
    proxies: Proxies,
    token_address: str,
) -> Result[int]:
    """
    Fetch the number of decimal places for a token.

    This function retrieves the decimal precision for a token on a given network.
    Currently supports EVM-compatible networks and Solana.

    Args:
        network: The blockchain network the token exists on
        nodes: RPC nodes to use for the request
        proxies: Proxy configuration for the request
        token_address: The address of the token

    Returns:
        Result containing the number of decimals as an integer on success, or an error message
    """
    if network.is_evm_network():
        return await eth_retry.erc20_decimals(RETRIES_DECIMALS, nodes, proxies, token=token_address, timeout=TIMEOUT_DECIMALS)
    if network == NETWORK_SOLANA:
        return await sol_retry.get_token_decimals(RETRIES_DECIMALS, nodes, proxies, token=token_address, timeout=TIMEOUT_DECIMALS)
    return Result.err("Unsupported network")
