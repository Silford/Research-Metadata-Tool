"""Command-line interface for the Research Metadata Toolkit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import argparse
import os
import sys
from tkinter import Tk, filedialog

from research_metadata_toolkit.toolkit.doi import process_doi_file
from research_metadata_toolkit.toolkit.encoding import fix_encoding
from research_metadata_toolkit.toolkit.urls import process_url_file
from research_metadata_toolkit.toolkit.utils.logging import configure_logging, get_logger

LOGGER = get_logger(__name__)
APP_NAME = "Research Metadata Toolkit"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Clean, validate, enrich, and analyze scholarly metadata"


@dataclass(frozen=True)
class ToolCommand:
    """CLI registration for one toolkit workflow."""

    key: str
    label: str
    description: str
    default_output: str
    handler: Callable[[str, str], str]


def _write(message: str = "") -> None:
    sys.stdout.write(f"{message}\n")


def _pick_excel_file() -> str:
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Excel File",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
    )
    root.destroy()
    return file_path


def _get_output_path(default_name: str = "output.xlsx") -> str:
    output_name = input(f"Output filename [{default_name}]: ").strip()
    if not output_name:
        output_name = default_name
    if not output_name.endswith(".xlsx"):
        output_name += ".xlsx"
    return str(Path.cwd() / output_name)


def _pause() -> None:
    input("\nPress Enter to return to the main menu...")


def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _print_header() -> None:
    _write()
    _write(APP_NAME.upper())
    _write(f"v{APP_VERSION} | {APP_SUBTITLE}")
    _write("=" * 72)


def _run_interactive_tool(command: ToolCommand) -> None:
    input_file = _pick_excel_file()
    if not input_file:
        LOGGER.warning("No file selected.")
        return
    output_file = _get_output_path(command.default_output)
    LOGGER.info("%s", command.label)
    LOGGER.info("Input: %s", input_file)
    LOGGER.info("Output: %s", output_file)
    command.handler(input_file, output_file)
    LOGGER.info("Saved results to: %s", output_file)


def build_registry() -> list[ToolCommand]:
    """Return registered toolkit workflows for the interactive CLI."""

    return [
        ToolCommand("encoding", "Fix text encoding", "Clean mojibake in Title and Authors", "output.xlsx", fix_encoding),
        ToolCommand("doi", "DOI enrichment", "Query DOI metadata and flag Caribbean links", "output.xlsx", process_doi_file),
        ToolCommand("urls", "URL validation", "Inspect URLs, DOI metadata, and pages", "output.xlsx", process_url_file),
    ]


def interactive_menu() -> None:
    """Run the numbered interactive CLI menu."""

    commands = build_registry()
    while True:
        _clear_screen()
        _print_header()
        _write("Choose a workflow for your Excel file.")
        _write()
        for index, command in enumerate(commands, start=1):
            _write(f"{index}. {command.label} - {command.description}")
        _write(f"{len(commands) + 1}. Exit")

        choice = input("\nSelect an option: ").strip()
        if choice == str(len(commands) + 1):
            LOGGER.info("Goodbye.")
            break
        try:
            command = commands[int(choice) - 1]
        except (ValueError, IndexError):
            LOGGER.error("Invalid option. Choose a listed number.")
            _pause()
            continue
        try:
            _run_interactive_tool(command)
        except Exception as exc:
            LOGGER.error("Operation failed: %s", exc)
        _pause()


def build_parser() -> argparse.ArgumentParser:
    """Build the non-interactive command parser."""

    parser = argparse.ArgumentParser(description=APP_SUBTITLE)
    subparsers = parser.add_subparsers(dest="command")
    for command in build_registry():
        subparser = subparsers.add_parser(command.key, help=command.description)
        subparser.add_argument("input_file", help="Input Excel workbook")
        subparser.add_argument("output_file", help="Output Excel workbook")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Research Metadata Toolkit CLI."""

    configure_logging()
    args_list = sys.argv[1:] if argv is None else argv
    if not args_list:
        interactive_menu()
        return 0

    parser = build_parser()
    args = parser.parse_args(args_list)
    if not args.command:
        interactive_menu()
        return 0

    registry = {command.key: command for command in build_registry()}
    registry[args.command].handler(args.input_file, args.output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
