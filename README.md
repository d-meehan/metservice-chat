# metservice-chat
A chatbot interface integrated with Metservice API to allow a user to interact with weather data through natural language

## Pre-requisites
- Python 3.12 or higher
- Poetry

## Installation
1. Clone the repository

```zsh
git clone git@github.com:d-meehan/metservice-chat.git
```

2. Create a virtual environment and install dependencies

```zsh
pyenv install 3.12
pyenv local 3.12
poetry config virtualenvs.in-project true
poetry install
```

3. Activate the virtual environment

```zsh
poetry shell
```

4. Set the environment variables

Create a .env file in the root with:
METSERVICE_KEY
OPENAI_API_KEY
GOOGLE_MAPS_API_KEY

5. Run the application

```zsh
python -m src.app.presentation.overview
```
