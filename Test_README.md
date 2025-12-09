# 🚀 envsafe — Safe, typed environment variable loading for Python

## 🔧 Quick Example

```python
from envsafe import env, EnvError
try:
    DEBUG = env.bool("DEBUG", default=False)
    PORT = env.int("PORT", required=True, min=1, max=65535)
    DATABASE_URL = env.url("DATABASE_URL", required=True)
    MODE = env.choice("MODE", choices=["dev", "prod"], default="dev")
    ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])
except EnvError as e:
    raise SystemExit(f"Configuration error: {e}")
```
---

## 📘 Supported Types

| Method         | Description                                      |
|----------------|--------------------------------------------------|
| `env.str()`    | Reads string values, supports required/default   |
| `env.int()`    | Validates integers, min/max constraints          |
| `env.float()`  | Float validation                                 |
| `env.bool()`   | Converts truthy/falsy strings to booleans        |
| `env.url()`    | Validates URL format + allowed schemes           |
| `env.choice()` | Ensures value is one of an allowed set           |
| `env.list()`   | Comma-separated strings → Python list            |

---

## 🔥 Advanced Example

```python
CONFIG = {
    "debug": env.bool("DEBUG", default=False),
    "workers": env.int("WORKERS", default=4, min=1, max=32),
    "api_url": env.url("API_URL", required=True, schemes=["https"]),
    "mode": env.choice("MODE", choices=["dev", "staging", "prod"]),
    "allowed_hosts": env.list("ALLOWED_HOSTS", default=["localhost"]),
}
```

---

# 🧪 Testing

envsafe includes automated tests and a manual test script so you can verify behavior easily.

## 1. Automated Test Suite (pytest)

### Create and activate a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -e .
pip install pytest
```

### Run the tests

```bash
pytest
```

Expected output:

```
7 passed in X.XXs
```

---

## 2. Manual Testing (test_envsafe_manual.py)

Run:

```bash
python test_envsafe_manual.py
```

### Output WITHOUT environment variables:

```
DEBUG: False
PORT: 8000
DATABASE_URL: None
MODE: dev
ALLOWED_HOSTS: ['localhost']
```

---

## 3. Testing WITH environment variables

### macOS / Linux

```bash
export DEBUG=true
export PORT=9001
export DATABASE_URL="https://example.com"
export MODE=prod
export ALLOWED_HOSTS="example.com, api.example.com"

python test_envsafe_manual.py
```

### Windows PowerShell

```powershell
setx DEBUG true
setx PORT 9001
setx DATABASE_URL "https://example.com"
setx MODE prod
setx ALLOWED_HOSTS "example.com, api.example.com"

python test_envsafe_manual.py
```

### Expected output:

```
DEBUG: True
PORT: 9001
DATABASE_URL: https://example.com
MODE: prod
ALLOWED_HOSTS: ['example.com', 'api.example.com']
```

---

## 4. Fake Environment Testing (no real env variables needed)

```python
from envsafe import Env

fake_env = Env(source={
    "DEBUG": "yes",
    "PORT": "9000",
})

assert fake_env.bool("DEBUG") is True
assert fake_env.int("PORT") == 9000
```

This is useful for unit testing other applications that depend on envsafe.

---

## 5. Cleaning Up

Remove Python cache folders:

```bash
find . -name "__pycache__" -exec rm -rf {} +
```

Deactivate your virtual environment:

```bash
deactivate
```

---

# 📄 License

MIT License - free for personal and commercial use.

---

# 🤝 Contributing

Pull requests and issues are welcome!  
If you encounter something interesting or want a new validator type, feel free to open an issue.

