# Dictionarian CLI and Python SDK

The commercial client for generating data dictionaries on the machine that can reach the database. It depends on the existing `dictionarian-ai` engine, uses Dictionarian prepaid credits for managed inference, and never asks customers for OpenAI, Anthropic, Gemini, or other model-provider credentials.

## Private alpha flow

```bash
dictionarian auth login
dictionarian init
export DICTIONARIAN_DB_PASSWORD='use-your-secret-manager-in-production'
dictionarian plan
dictionarian generate
```

`auth login` opens the account dashboard, accepts the product token through a hidden prompt, validates it, and stores it in the operating-system keyring. Do not pass tokens as command arguments or save them in `dictionarian.toml`.

## Privacy defaults

Database credentials, connections, and SQL queries stay on the local machine. Schema metadata is sent to Dictionarian for managed inference. Representative row values, source excerpts, absolute source paths, and onboarding documents are excluded by default.

Run `dictionarian plan` before generation to see the categories that can cross the network. Explicitly setting `profile_sample_values = true` or `include_code_context = true` expands that boundary.

## Install from source during development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[postgres,dev]'
```

The release pipeline builds standalone macOS and Linux binaries, creates checksums and SBOMs, and signs each release. The Homebrew formula is activated after the first release supplies its final checksums.

## Python SDK

```python
from dictionarian_cli import DictionarianClient, load_project_config, run_generation

project = load_project_config("dictionarian.toml")
token = "load this from a secret manager"

with DictionarianClient(token, api_url=project.api_url) as client:
    print(client.balance())

run_generation(project, token)
```

## Distribution

Homebrew, after the first signed release:

```bash
brew install dictionarian-ai/tap/dictionarian
```

Verified curl download, after installer hosting is configured:

```bash
curl -fsSLo dictionarian-install.sh https://get.dictionarian.ai/install.sh
less dictionarian-install.sh
sh dictionarian-install.sh
```

The installer uses a versioned GitHub Release, downloads into a temporary directory, verifies SHA-256, and installs without `sudo` into `~/.local/bin` by default.
