# datasift-py

**Python-native fluent API for data conversion, querying, manipulation, and validation. Zero dependencies.**

[![PyPI version](https://img.shields.io/pypi/v/datasift-py.svg)](https://pypi.org/project/datasift-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/datasift-py.svg)](https://pypi.org/project/datasift-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why datasift-py?

| Feature | datasift-py | dataconv | pureyq | python-benedict | yq | dasel |
|---|---|---|---|---|---|---|
| Fluent / chainable API | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Zero dependencies | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Python-native query syntax | ✅ | ❌ | ❌ (jq) | ❌ | ❌ (jq) | ❌ |
| JSON/YAML/TOML/CSV/XML | ✅ | ✅ | ⚠️ (partial) | ✅ | ❌ | ✅ |
| True streaming (CSV/JSONL) | ✅ | ❌ | ❌ | ❌ | ❌ | ⚠️ |
| Zero-dep schema validation | ✅ | ❌ | ❌ | ⚠️ (pydantic) | ❌ | ❌ |
| CLI + Library | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

## Quick start

```bash
pip install datasift-py
```

```python
from datasift import Data

# Convert JSON to CSV with a fluent chain
(
    Data("users.json")
    .filter(age__gt=30)
    .select("name", "email")
    .to("adults.csv")
)
```

```python
from datasift import Stream

# Stream a 10 GB CSV without loading it into memory
(
    Stream.from_csv("huge.csv")
    .filter(age__gt=30)
    .select("name", "email")
    .to_csv("filtered.csv")
)
```

```python
from typing import List
from typing_extensions import TypedDict
from datasift import Data

class User(TypedDict):
    name: str
    age: int

Data("users.json").expect(List[User]).to("validated.csv")
```

## License

MIT