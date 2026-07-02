# Research Metadata Toolkit

Research Metadata Toolkit is a Python package and command-line tool for cleaning, validating, enriching, and analyzing scholarly metadata in Excel workbooks.

Current workflows include:

- Fix encoding issues in `Title` and `Authors` columns.
- Enrich DOI rows with OpenAlex and Crossref metadata.
- Review article URLs, discover DOI/page metadata, and flag Caribbean affiliations.

## Intended Users

- Researchers and graduate students
- Librarians and repository teams
- Systematic review teams
- Bibliometric analysts
- Research administrators

## Installation

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

For development and tests:

```powershell
python -m pip install -e .
python -m pip install pytest
python -m pytest
```

## Usage

Interactive menu:

```powershell
research-metadata-toolkit
```

Module entry point:

```powershell
python -m research_metadata_toolkit
```

Non-interactive commands:

```powershell
python -m research_metadata_toolkit encoding input.xlsx output.xlsx
python -m research_metadata_toolkit doi input.xlsx output.xlsx
python -m research_metadata_toolkit urls input.xlsx output.xlsx
```

Package imports:

```python
from research_metadata_toolkit import fix_encoding, process_doi_file, process_url_file
```

## Architecture

```text
research_metadata_toolkit/
  cli.py
  main.py
  data/
    aliases.json
    countries.json
    universities.json
  toolkit/
    affiliations/   Country and institution matching
    api/            OpenAlex and Crossref API access
    config/         Shared runtime settings
    doi/            DOI enrichment workflow
    encoding/       Text encoding cleanup workflow
    urls/           URL metadata and affiliation workflow
    utils/          Excel, HTTP, logging, progress, DOI, and text helpers
tests/
```

The CLI is registry-driven. To add a new workflow, create a module with a public function, then register it in `research_metadata_toolkit/cli.py`.

## Public Functions

- `fix_encoding(input_file, output_file, columns_to_fix=("Title", "Authors"))`
- `process_doi_file(input_file, output_file=None, max_workers=None, settings=DEFAULT_SETTINGS)`
- `process_url_file(input_file, output_file, max_workers=None, settings=DEFAULT_SETTINGS)`

## Configuration

Shared defaults live in `research_metadata_toolkit/toolkit/config/settings.py`:

- DOI and URL worker counts
- HTTP timeout and retry settings
- Retry backoff
- URL access checking behavior
- HTTP headers and connection pool size

Country and university data live in JSON files under `research_metadata_toolkit/data/`.

## Error Handling And Logging

Core modules use Python logging instead of direct `print()` calls. The CLI configures `INFO`, `WARNING`, and `ERROR` output for users.

Excel loading/saving errors raise `ExcelFileError`. Missing required columns raise `MissingColumnError`. Network/API failures are logged and handled row-by-row so batch processing can continue.

## Examples

Fix text encoding:

```python
from research_metadata_toolkit import fix_encoding

fix_encoding("raw_metadata.xlsx", "clean_metadata.xlsx")
```

Run DOI enrichment:

```python
from research_metadata_toolkit import process_doi_file

process_doi_file("records.xlsx", "doi_results.xlsx")
```

Run URL affiliation review:

```python
from research_metadata_toolkit import process_url_file

process_url_file("records.xlsx", "url_results.xlsx")
```

## Contributing

See `CONTRIBUTING.md` for development setup, coding standards, and pull request guidance.

## License

This project is licensed under the MIT License. See `LICENSE`.
