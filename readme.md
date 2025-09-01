# IE Proj.

## Dart

- [DART-FSS Documentation](https://dart-fss.readthedocs.io/en/latest/index.html)

## Set up API Keys

1. Sign up for a DART account and obtain your API key.
2. Create a `.env` file in the root of your project directory.
3. Add your API key to the `.env` file in the following format:

```
DART_API_KEY=your_api_key_here
```

## Set up `uv` virtual environment

```zsh
uv venv # create virtual environment
uv pip install -r requirements.txt # install dependencies
source .venv/bin/activate # activate virtual environment (mac)
```

if you use window, you need to activate the virtual environment with:

```shell
.venv\Scripts\activate
```
