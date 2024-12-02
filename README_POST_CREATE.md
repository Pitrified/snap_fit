# Template instructions

## Set up a new Python project

Clone the `python-project-template` repo.

```bash
git clone git@github.com:Pitrified/python-project-template.git
```

From outside the repo, run the
[rename_project.py](meta/rename_project.py)
script to rename the project.

```bash
python snap_fit/meta/rename_project.py
```

By this point, the project is already set up with the new name.
This README file will be copied in `README_POST_CREATE.md`,
with the name of the project updated.

Go to the new folder:

```bash
cd snap_fit
```

Install the project:

```bash
poetry install
```

<!-- Install the optional dependencies with the following command: -->
<!-- {{optional_dependencies}} -->
<!-- TODO automagically generate the optional dependencies list -->

Install the required dependencies:
(actually already done by the `poetry install` command, the existing dependencies of the template project are kept in the `pyproject.toml` file)
So this command is only needed to bump the versions of the dependencies.

```bash
poetry add loguru
poetry add --group dev pytest
```

Initialize the git repository, set the identity, and make the first commit:

```bash
git init
git add .
git add **/.gitkeep -f
# gitid ...
git commit -m "Initial commit"
```

## Install additional dependencies

Install the dependencies you want with the following commands

Log and formatting dependencies

```bash
poetry add loguru rich tqdm
```

LLM dependencies

```bash
poetry add transformers accelerate
poetry add torch
poetry add \
    chromadb \
    langchain \
    langchain-chroma \
    langchain-community \
    langchain-huggingface \
    langchain-ollama ollama \
    langchain-openai \
    langgraph \
    sentence_transformers
```

Data dependencies

```bash
poetry add \
    pandas numpy matplotlib seaborn scikit-learn \
    plotly altair bokeh
    kaleido==0.2.1
```

Web dependencies

```bash
poetry add fastapi uvicorn
poetry add streamlit
```

Notebook dependencies

```bash
poetry add ipykernel ipywidgets nbformat
```

Scraping dependencies

```bash
poetry add \
    beautifulsoup4 lxml \
    httpx \
    requests \
    scrapy \
    aiohttp
```

Test dependencies

```bash
poetry add --group dev pytest
poetry add --group dev pytest-cov
```
