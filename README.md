# envsafe — Safe, typed environment variable loading for Python

**envsafe** is a tiny, dependency-free library that makes environment variable handling **safe, predictable, and developer-friendly**.

Instead of working with raw strings from `os.environ`, envsafe provides **typed, validated configuration** with clear errors when something is missing or invalid.

---

## Why envsafe?

- **Fail fast** on missing or invalid configuration  
- **Typed access** (`int`, `bool`, `float`, `url`, `list`, `json`, `email`, `bytes`, `duration` and more)  
- **Zero dependencies** — lightweight & framework-agnostic  
- **Built-in `.env` file loading** — no need for python-dotenv  
- **Simple, explicit API** (no black magic)  
- **Fully tested** and production-ready  

---

## Installation

```bash
pip install envsafe
```

---

## Quick Start

```python
from envsafe import env, load_dotenv

# Optional: Load from .env file
load_dotenv()

# Read typed environment variables
DEBUG = env.bool("DEBUG", default=False)
PORT = env.int("PORT", default=8000)
DATABASE_URL = env.url("DATABASE_URL", required=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])
```

---

## The Problem envsafe Solves

Environment variables are **always strings**. This causes bugs:

```python
import os

# Bug 1: "false" is truthy!
os.environ["DEBUG"] = "false"
if os.environ.get("DEBUG"):  # TRUE! Non-empty string
    print("Debug mode")  # This runs even when DEBUG=false!

# Bug 2: Type errors
os.environ["PORT"] = "8080"
port = os.environ.get("PORT")
new_port = port + 1  # ERROR: can't add string + int
```

**envsafe fixes this:**

```python
from envsafe import env

DEBUG = env.bool("DEBUG")  # Returns actual False
PORT = env.int("PORT")     # Returns actual 8080
```

---

## API Reference

### Basic Types

#### `env.str(key, *, default=None, required=False, allow_empty=False)`

```python
APP_NAME = env.str("APP_NAME", default="MyApp")
SECRET = env.str("SECRET_KEY", required=True)
```

#### `env.int(key, *, default=None, required=False, min=None, max=None)`

```python
PORT = env.int("PORT", default=8000)
WORKERS = env.int("WORKERS", default=4, min=1, max=32)
```

#### `env.float(key, *, default=None, required=False, min=None, max=None)`

```python
RATE = env.float("RATE_LIMIT", default=1.0, min=0.1, max=100.0)
```

#### `env.bool(key, *, default=None, required=False)`

Accepts: `true/false`, `1/0`, `yes/no`, `on/off`, `t/f`, `y/n`

```python
DEBUG = env.bool("DEBUG", default=False)
```

---

### Advanced Types

#### `env.url(key, *, default=None, required=False, schemes=None)`

```python
API_URL = env.url("API_URL", required=True)
DB_URL = env.url("DATABASE_URL", schemes=["postgres", "mysql"])
```

#### `env.list(key, *, default=None, required=False, separator=",", strip=True)`

```python
# HOSTS="localhost, example.com, api.example.com"
HOSTS = env.list("HOSTS")  # ["localhost", "example.com", "api.example.com"]

# TAGS="a;b;c"
TAGS = env.list("TAGS", separator=";")  # ["a", "b", "c"]
```

#### `env.choice(key, *, choices, default=None, required=False, case_sensitive=False)`

```python
ENV = env.choice("ENV", choices=["development", "staging", "production"])
LOG_LEVEL = env.choice("LOG_LEVEL", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
```

#### `env.json(key, *, default=None, required=False)`

```python
# CONFIG='{"debug": true, "port": 8080}'
CONFIG = env.json("CONFIG")  # {"debug": True, "port": 8080}
```

#### `env.email(key, *, default=None, required=False)`

```python
ADMIN_EMAIL = env.email("ADMIN_EMAIL", required=True)
```

#### `env.port(key, *, default=None, required=False)`

Shortcut for `env.int()` with min=1, max=65535.

```python
PORT = env.port("PORT", default=8080)
```

#### `env.path(key, *, default=None, required=False, must_exist=False, must_be_file=False, must_be_dir=False)`

```python
LOG_DIR = env.path("LOG_DIR", must_be_dir=True)
CONFIG_FILE = env.path("CONFIG_FILE", must_be_file=True, must_exist=True)
```

#### `env.bytes(key, *, default=None, required=False)`

Parse byte sizes like `10MB`, `1GB`, `500KB`.

```python
# MAX_UPLOAD="10MB"
MAX_UPLOAD = env.bytes("MAX_UPLOAD")  # 10485760 (bytes)
```

#### `env.duration(key, *, default=None, required=False)`

Parse durations like `30s`, `5m`, `2h`, `1d`.

```python
# TIMEOUT="30s"
TIMEOUT = env.duration("TIMEOUT")  # 30.0 (seconds)

# CACHE_TTL="5m"  
CACHE_TTL = env.duration("CACHE_TTL")  # 300.0 (seconds)
```

#### `env.regex(key, *, pattern, default=None, required=False)`

```python
API_KEY = env.regex("API_KEY", pattern=r"^sk-[a-z0-9]+$")
```

#### `env.custom(key, parser, *, default=None, required=False)`

```python
from datetime import datetime

def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")

START_DATE = env.custom("START_DATE", parse_date)
```

---

### Loading .env Files

```python
from envsafe import load_dotenv, env

# Load from .env (default)
load_dotenv()

# Load from custom path
load_dotenv(".env.local")

# Override existing environment variables
load_dotenv(".env", override=True)

# Now use env as normal
DEBUG = env.bool("DEBUG")
```

**.env file format:**

```env
# Comments are supported
DEBUG=true
PORT=8080
DATABASE_URL="postgres://localhost/mydb"
SECRET_KEY='my-secret-key'
export APP_NAME=MyApp  # export prefix is handled
```

---

## Error Handling

```python
from envsafe import env, EnvError

try:
    PORT = env.int("PORT", required=True)
except EnvError as e:
    print(f"Configuration error: {e}")
```

Error messages are clear and helpful:

```
Missing required environment variable: DATABASE_URL
PORT must be an integer, got 'abc'
PORT must be >= 1, got 0
ENV must be one of ['development', 'production'], got 'invalid'
ADMIN_EMAIL must be a valid email address, got 'not-an-email'
```

---

## Testing

Use a custom source for testing:

```python
from envsafe import Env

test_env = Env(source={
    "DEBUG": "true",
    "PORT": "9000",
})

assert test_env.bool("DEBUG") == True
assert test_env.int("PORT") == 9000
```

---

## Real-World Example

```python
# config.py
from envsafe import env, load_dotenv

load_dotenv()

class Config:
    # App
    APP_NAME = env.str("APP_NAME", default="MyApp")
    DEBUG = env.bool("DEBUG", default=False)
    ENV = env.choice("ENV", choices=["development", "staging", "production"], default="development")
    
    # Server
    HOST = env.str("HOST", default="0.0.0.0")
    PORT = env.port("PORT", default=8000)
    
    # Database
    DATABASE_URL = env.url("DATABASE_URL", required=True, schemes=["postgres"])
    
    # Security
    SECRET_KEY = env.str("SECRET_KEY", required=True)
    ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])
    
    # Performance
    WORKERS = env.int("WORKERS", default=4, min=1, max=32)
    REQUEST_TIMEOUT = env.duration("REQUEST_TIMEOUT", default=30.0)
    MAX_UPLOAD_SIZE = env.bytes("MAX_UPLOAD_SIZE", default=10 * 1024 * 1024)
    
    # Email
    SMTP_HOST = env.str("SMTP_HOST", default="smtp.gmail.com")
    SMTP_PORT = env.port("SMTP_PORT", default=587)
    ADMIN_EMAIL = env.email("ADMIN_EMAIL", required=True)
    
    # Feature flags
    ENABLE_CACHE = env.bool("ENABLE_CACHE", default=True)
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
