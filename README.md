# Max Bot - Long Polling Example

#### Setting up .env file

```bash
cp .env.example .env
```

#### 1. Install UV:
```bash
pip install uv
```

#### 2. Install all dependencies from pyproject.toml
```bash
uv sync
```

#### 3. Activate virtual env
```bash
source .venv/bin/activate
```

This will automatically:
- create a virtual environment (`.venv`)
- install all packages
- lock versions exactly as in `uv.lock`

### Running LightRAG server locally

After installing:

```bash
lightrag-server
```
