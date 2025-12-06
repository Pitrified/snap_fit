# Snap fit

## Installation

To install the package, run the following command:

```bash
poetry install
```

## Setup

To setup the package, create a `.env` file in `~/cred/snap_fit/.env` with the following content:

```bash
SNAP_FIT_SAMPLE_ENV_VAR=sample
```

And for VSCode to recognize the environment file, add the following line to the
workspace [settings file](.vscode/settings.json):

```json
"python.envFile": "/home/pmn/cred/snap_fit/.env"
```

Note that the path to the `.env` file should be absolute.

## Pre-commit

To install the pre-commit hooks, run the following command:

```bash
pre-commit install
```

Run against all the files:

```bash
pre-commit run --all-files
```

## Linting

Use pyright for type checking:

```bash
uv run pyright
```

Use ruff for linting:

```bash
uv run ruff check --fix
uv run ruff format
```

## Testing

To run the tests, use the following command:

```bash
poetry run pytest
```

or use the VSCode interface.

## IDEAs
