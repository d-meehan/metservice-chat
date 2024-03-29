# metservice-chat
A chatbot interface integrated with Metservice API to allow a user to interact with weather data through natural language

## Pre-requisites
- Python 3.10 or higher
- Poetry

## Installation
1. Clone the repository

```zsh
git clone git@github.com:d-meehan/metservice-chat.git
```

2. Create a virtual environment and install dependencies

```zsh
pyenv install 3.10
pyenv local 3.10
poetry config virtualenvs.in-project true
poetry install
```

3. Activate the virtual environment

```zsh
poetry shell
```

4. Set the environment variables

Create a .env file in the root with:
METSERVICE_API_KEY
OPENAI_API_KEY

5. Add src to the PYTHONPATH

```zsh
export PYTHONPATH="${PYTHONPATH}:/src"
```

6. Run the application

```zsh
python3 src/app/main.py
```
