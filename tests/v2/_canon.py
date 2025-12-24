import json
import hashlib

def canonical_json_dumps(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def hash_canonical(obj) -> str:
    return hashlib.sha256(canonical_json_dumps(obj).encode("utf-8")).hexdigest()
