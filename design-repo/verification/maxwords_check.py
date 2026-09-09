"""
Round 3 addition — real per-instance maxWords enforcement.

schema/pagespec.schema.json annotates dozens of fields with a custom
`x-maxWordsRoleBound` keyword (72 occurrences at last count). Custom "x-" prefixed
keywords are, by JSON Schema convention, pure annotations: standard validators
(including this repo's own `jsonschema.Draft7Validator` usage in
schema/validate_schema.py and verification/round2_adversarial_tests.py) never
enforce them. Before this file, NO code anywhere in the repo counted words in an
actual content string against its declared bound -- not a runtime check on a
generated PageSpec, and not even a static check on the one example the repo ships
(schema/example.pagespec.json). verify_all.py's existing "[4] maxWords vs
typography-role ceiling" check is a different, narrower thing: it only cross-checks
each *section's* declared `constraints.maxWords` value against the widest plausible
typography-role ceiling group -- it never looks at a real string's actual word
count.

This module closes that gap: for every node in a PageSpec-shaped document, it
walks the matching per-type schema branch alongside the actual content payload,
finds every field carrying `x-maxWordsRoleBound`, counts words in the real string
value with str.split(), and flags any that exceed the bound.
"""
import json, os, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_schema():
    return json.load(open(os.path.join(REPO, "schema", "pagespec.schema.json")))


def _content_schema_for_type(schema, type_id):
    for block in schema["properties"]["nodes"]["items"]["allOf"]:
        try:
            if block["if"]["properties"]["type"]["const"] == type_id:
                return block["then"]["properties"].get("content")
        except (KeyError, TypeError):
            continue
    return None


def _walk(field_schema, value, path, issues):
    if not isinstance(field_schema, dict):
        return
    bound = field_schema.get("x-maxWordsRoleBound")
    if bound is not None and isinstance(value, str):
        wc = len(value.split())
        if wc > bound:
            issues.append(f"{path}: {wc} words (max {bound}) -- {value!r}")
    props = field_schema.get("properties")
    if isinstance(props, dict) and isinstance(value, dict):
        for k, sub in props.items():
            if k in value:
                _walk(sub, value[k], f"{path}.{k}", issues)
    items_schema = field_schema.get("items")
    if items_schema is not None and isinstance(value, list):
        for idx, item_val in enumerate(value):
            _walk(items_schema, item_val, f"{path}[{idx}]", issues)


def check_document(doc, schema, label="doc"):
    issues = []
    for i, node in enumerate(doc.get("nodes", [])):
        content_schema = _content_schema_for_type(schema, node.get("type"))
        if content_schema is None:
            continue
        _walk(content_schema, node.get("content", {}), f"{label}.nodes[{i}]({node.get('type')})", issues)
    return issues


def run():
    schema = load_schema()
    issues = []
    example = json.load(open(os.path.join(REPO, "schema", "example.pagespec.json")))
    issues += check_document(example, schema, label="schema/example.pagespec.json")
    return issues


if __name__ == "__main__":
    issues = run()
    print(f"[maxwords_check] {len(issues)} violation(s)")
    for i in issues:
        print(" -", i)
    sys.exit(1 if issues else 0)
