# CLI

The `datasift` command-line tool provides conversion and querying.

## Convert

```bash
datasift convert input.json output.yaml
datasift convert input.csv output.xml
datasift convert input.json output.csv -q "users[?age > 30]"
```

## Query

```bash
datasift query data.json "users[0].name"
datasift query data.yaml "config.db.host" -of json
datasift query data.json "users[*].name" -of yaml
```

## Formats

```bash
datasift formats
```

Output:

```
csv
json
jsonl
toml
xml
yaml
```

## Using stdin / stdout

Use `"-"` as the input or output path to read from stdin or write to stdout:

```bash
cat data.json | datasift convert - output.yaml
datasift query data.json "users[*].name" -of json > names.json
```