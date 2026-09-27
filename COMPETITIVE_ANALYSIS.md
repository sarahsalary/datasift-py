# Competitive Analysis — datasift-py

## Position

datasift-py is **not** the first Python library for data conversion + query.
It is the **first to offer a fluent, chainable, Python-native API**
for data conversion, filtering, selection, sorting, transformation,
streaming, and schema validation — with zero dependencies.

## Key Differentiator

| Feature | datasift-py | dataconv | pureyq | python-benedict | yq | dasel |
|---|---|---|---|---|---|---|
| Fluent / chainable API | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Zero dependencies | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Python-native query syntax | ✅ | ❌ | ❌ (jq) | ❌ | ❌ (jq) | ❌ |
| JSON/YAML/TOML/CSV/XML | ✅ | ✅ | ⚠️ (partial) | ✅ | ❌ | ✅ |
| True streaming (CSV/JSONL) | ✅ | ❌ | ❌ | ❌ | ❌ | ⚠️ |
| Zero-dep schema validation | ✅ | ❌ | ❌ | ⚠️ (pydantic) | ❌ | ❌ |
| CLI + Library | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Type hints | ✅ | ❌ | ❌ | ✅ | ❌ | N/A |
| Source available | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |

## What datasift-py does that others don't

1. **Fluent API**: `Data("users.json").filter(age__gt=30).select("name").sort("-age").to("out.csv")`
2. **Python-native query syntax**: `filter(age__gt=30)` instead of `jq` or JSONPath.
3. **Zero dependencies with full format support**: unlike pureyq (query only) or python-benedict (dependencies).
4. **CLI + Library with identical API**: unlike python-benedict (library only) or yq (CLI only).
5. **True streaming**: only library with zero-dep streaming for CSV/JSONL.
6. **Zero-dep schema validation**: only library with built-in validation without pydantic.

## Weaknesses to address

- YAML parser is a subset, not full YAML 1.2.
- TOML fallback parser is minimal.
- No XML namespace support yet.
- No async API.
- No plugin system for custom formats.

## Roadmap

- [ ] Full YAML 1.2 support (optional PyYAML integration).
- [ ] XML namespace support.
- [ ] Async streaming API.
- [ ] Plugin system for custom formats.
- [ ] Benchmark suite.