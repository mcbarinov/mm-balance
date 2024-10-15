from decimal import Decimal

from mm_eth import erc20, rpc
from mm_std import Ok, Result


def get_native_balance(nodes: list[str], address: str, proxies: list[str], round_ndigits: int) -> Result[Decimal]:
    return rpc.eth_get_balance(nodes, address, proxies=proxies, attempts=5, timeout=10).and_then(
        lambda b: Ok(round(Decimal(b / 10**18), round_ndigits)),
    )


def get_token_balance(
    nodes: list[str], wallet_address: str, token_address: str, decimals: int, proxies: list[str], round_ndigits: int
) -> Result[Decimal]:
    return erc20.get_balance(
        nodes,
        token_address,
        wallet_address,
        proxies=proxies,
        attempts=5,
        timeout=10,
    ).and_then(
        lambda b: Ok(round(Decimal(b / 10**decimals), round_ndigits)),
    )


def get_token_decimals(nodes: list[str], token_address: str, proxies: list[str]) -> Result[int]:
    return erc20.get_decimals(nodes, token_address, timeout=10, proxies=proxies, attempts=5)


# def get_balance(
#         address: str, token_address: str | None, config: Config, progress: Progress | None = None, task_id: TaskID | None = None
# ) -> Result[Decimal]:
#     res: Result[Decimal]
#
#     if token_address is not None:
#
#     else:
#         res = rpc.eth_get_balance(config.nodes[Network.ETH], address, proxies=config.proxies, attempts=5, timeout=10).and_then(
#             lambda b: Ok(round(Decimal(b / 10 ** 18), config.round_ndigits)),
#         )
#
#     if task_id is not None and progress is not None:
#         progress.update(task_id, advance=1)
#     return res
