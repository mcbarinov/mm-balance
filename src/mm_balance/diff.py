import json
import re
from decimal import Decimal
from pathlib import Path

from deepdiff.diff import DeepDiff
from mm_print import print_json, print_plain, print_table
from pydantic import BaseModel, RootModel

from mm_balance.result import Balance, BalancesResult
from mm_balance.utils import PrintFormat


class BalancesDict(RootModel[dict[str, dict[str, dict[str, Decimal]]]]):  # network->ticker->address->balance
    def networks(self) -> set[str]:
        return set(self.model_dump().keys())

    def tickers(self, network: str) -> set[str]:
        return set(self.model_dump()[network].keys())

    def save_to_path(self, balances_file: Path) -> None:
        json.dump(self.model_dump(), balances_file.open("w"), default=str, indent=2)

    @staticmethod
    def from_balances_result(result: BalancesResult) -> BalancesDict:
        data: dict[str, dict[str, dict[str, Decimal]]] = {}  # network->ticker->address->balance
        for group in result.groups:
            if group.network not in data:
                data[group.network] = {}
            if group.ticker not in data[group.network]:
                data[group.network][group.ticker] = {}
            for address in group.addresses:
                if isinstance(address.balance, Balance):
                    data[group.network][group.ticker][address.address] = address.balance.balance
        return BalancesDict(data)

    @staticmethod
    def from_file(path: Path) -> BalancesDict:
        return BalancesDict(json.load(path.open("r")))


class Diff(BaseModel):
    network_added: list[str]
    network_removed: list[str]

    ticker_added: dict[str, list[str]]  # network -> tickers
    ticker_removed: dict[str, list[str]]  # network -> tickers

    address_added: dict[str, dict[str, list[str]]]  # network -> ticker -> addresses
    address_removed: dict[str, dict[str, list[str]]]  # network -> ticker -> addresses

    balance_changed: dict[str, dict[str, dict[str, tuple[Decimal, Decimal]]]]  # network->ticker->address->(old_value,new_value)

    def print(self, print_format: PrintFormat) -> None:
        match print_format:
            case PrintFormat.TABLE:
                self._print_table()
            case PrintFormat.JSON:
                self._print_json()
            case _:
                raise ValueError(f"Unsupported print format: {print_format}")

    def _print_table(self) -> None:
        if (
            not self.network_added
            and not self.network_removed
            and not self.ticker_added
            and not self.ticker_removed
            and not self.address_added
            and not self.address_removed
            and not self.balance_changed
        ):
            print_plain("Diff: no changes")
            return

        print_plain("\nDiff")

        if self.network_added:
            print_plain(f"networks added: {self.network_added}")
        if self.network_removed:
            print_plain(f"networks removed: {self.network_removed}")
        if self.ticker_added:
            print_plain(f"tickers added: {self.ticker_added}")
        if self.ticker_removed:
            print_plain(f"tickers removed: {self.ticker_removed}")
        if self.address_added:
            print_plain(f"addresses added: {self.address_added}")
        if self.address_removed:
            print_plain(f"addresses removed: {self.address_removed}")

        if self.balance_changed:
            rows = []
            for network in self.balance_changed:
                for ticker in self.balance_changed[network]:
                    for address in self.balance_changed[network][ticker]:
                        old_value, new_value = self.balance_changed[network][ticker][address]
                        rows.append([network, ticker, address, old_value, new_value, new_value - old_value])
            print_table(["Network", "Ticker", "Address", "Old", "New", "Change"], rows)

    def _print_json(self) -> None:
        # print_json(data=self.model_dump(), type_handlers=str) ?? default?
        print_json(data=self.model_dump())

    @staticmethod
    def calc(balances1: BalancesDict, balances2: BalancesDict) -> Diff:
        dd = DeepDiff(balances1.model_dump(), balances2.model_dump(), ignore_order=True)
        # Initialize empty collections for Diff fields.

        network_added = []
        network_removed = []
        ticker_added: dict[str, list[str]] = {}
        ticker_removed: dict[str, list[str]] = {}
        address_added: dict[str, dict[str, list[str]]] = {}
        address_removed: dict[str, dict[str, list[str]]] = {}
        balance_changed: dict[str, dict[str, dict[str, tuple[Decimal, Decimal]]]] = {}

        # Helper to extract keys from DeepDiff paths.
        def extract_keys(path: str) -> list[str]:
            # DeepDiff paths look like "root['network']['ticker']['address']"
            return re.findall(r"\['([^']+)'\]", path)

        # Process dictionary_item_added
        for path in dd.get("dictionary_item_added", []):
            keys = extract_keys(path)
            if len(keys) == 1:
                # New network added.
                network_added.append(keys[0])
            elif len(keys) == 2:
                # New ticker added under an existing network.
                network, ticker = keys
                ticker_added.setdefault(network, []).append(ticker)
            elif len(keys) == 3:
                # New address added under an existing network and ticker.
                network, ticker, address = keys
                address_added.setdefault(network, {}).setdefault(ticker, []).append(address)

        # Process dictionary_item_removed
        for path in dd.get("dictionary_item_removed", []):
            keys = extract_keys(path)
            if len(keys) == 1:
                network_removed.append(keys[0])
            elif len(keys) == 2:
                network, ticker = keys
                ticker_removed.setdefault(network, []).append(ticker)
            elif len(keys) == 3:
                network, ticker, address = keys
                address_removed.setdefault(network, {}).setdefault(ticker, []).append(address)

        # Process values_changed for balance differences.
        for path, change in dd.get("values_changed", {}).items():
            keys = extract_keys(path)
            if len(keys) != 3:
                continue
            network, ticker, address = keys
            balance_changed.setdefault(network, {}).setdefault(ticker, {})[address] = (
                Decimal(change["old_value"]),
                Decimal(change["new_value"]),
            )

        return Diff(
            network_added=sorted(network_added),
            network_removed=sorted(network_removed),
            ticker_added={k: sorted(v) for k, v in ticker_added.items()},
            ticker_removed={k: sorted(v) for k, v in ticker_removed.items()},
            address_added={k: {tk: sorted(vv) for tk, vv in v.items()} for k, v in address_added.items()},
            address_removed={k: {tk: sorted(vv) for tk, vv in v.items()} for k, v in address_removed.items()},
            balance_changed=balance_changed,
        )
