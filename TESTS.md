# TESTS

## Pubs :: Import

### Eugene, OR
```bash

curl -H "Accept: application/json" "http://127.0.0.1:8000/api/v1/pubs/import?latitude=44.05063&longitude=-123.10768&radius=10000"

```

### Springfield, OR
```bash

curl -H "Accept: application/json" "http://127.0.0.1:8000/api/v1/pubs/import?latitude=44.0569&longitude=-123.0039&radius=10000"

```

### Portland, OR
```bash

curl -H "Accept: application/json" "http://127.0.0.1:8000/api/v1/pubs/import?latitude=45.52413&longitude=-122.66825&radius=15000"

```

## Addresses :: Fix
```bash

curl -H "Accept: application/json" "http://127.0.0.1:8000/api/v1/pubs/fix_missing_addresses"

```


