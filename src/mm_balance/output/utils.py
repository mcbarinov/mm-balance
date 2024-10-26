from decimal import Decimal

from rich.progress import BarColumn, MofNCompleteColumn, Progress, TaskID, TextColumn


def format_number(value: Decimal, separator: str, extra: str | None = None) -> str:
    str_value = f"{value:,}".replace(",", separator)
    if extra == "$":
        return "$" + str_value
    elif extra == "%":
        return str_value + "%"
    return str_value


def create_progress_bar(disable: bool) -> Progress:
    return Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), MofNCompleteColumn(), disable=disable)


def create_progress_task(progress: Progress, description: str, total: int) -> TaskID:
    return progress.add_task("[green]" + description, total=total)
