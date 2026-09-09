import json, copy, os, sys
from jsonschema import Draft7Validator

# Derived from this script's own location (see verification/verify_all.py for why:
# a hardcoded absolute path here made this suite silently validate the ORIGINAL
# repo even when run from an extracted/relocated copy — Round 3 fix).
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
schema = json.load(open(f"{REPO}/schema/pagespec.schema.json"))
example = json.load(open(f"{REPO}/schema/example.pagespec.json"))

validator = Draft7Validator(schema)

def check(name, doc, expect_valid):
    errors = list(validator.iter_errors(doc))
    is_valid = len(errors) == 0
    status = "PASS" if is_valid == expect_valid else "FAIL"
    print(f"[{status}] {name}: expected_valid={expect_valid} actual_valid={is_valid}" + (f" (first error: {errors[0].message[:120]})" if errors else ""))
    return status == "PASS"

results = []

# 1. baseline example must validate cleanly
results.append(check("baseline example.pagespec.json validates", example, True))

# --- Adversarial mutation 1: wrong theme value ---
m1 = copy.deepcopy(example)
m1["theme"] = "dtai-dark"
results.append(check("adversarial: unlisted theme 'dtai-dark'", m1, False))

# --- Adversarial mutation 2: a card missing its real required field (product missing 'href') ---
m2 = copy.deepcopy(example)
for node in m2["nodes"]:
    if node["type"] == "related-products-grid":
        del node["content"]["products"][0]["href"]
results.append(check("adversarial: related-products-grid product missing required 'href'", m2, False))

# --- Adversarial mutation 3: motion declared without reducedMotionFallback ---
m3 = copy.deepcopy(example)
for node in m3["nodes"]:
    if node["type"] == "hero-product":
        del node["reducedMotionFallback"]
results.append(check("adversarial: hero-product motion without reducedMotionFallback", m3, False))

# --- Adversarial mutation 4: old bare-alias token reference instead of full canonical path ---
m4 = copy.deepcopy(example)
for node in m4["nodes"]:
    if node["type"] == "hero-product":
        node["motion"]["role"] = "--fade-up"  # bare alias, not tokens.10-semantic.motion-roles.roles.*
results.append(check("adversarial: bare-alias motion role reference '--fade-up'", m4, False))

# --- Adversarial mutation 5: unlisted / phantom section type ---
m5 = copy.deepcopy(example)
m5["nodes"].append({"type": "hero-parallax-experimental", "registryId": "section.hero-parallax-experimental", "content": {}})
results.append(check("adversarial: unlisted phantom section type 'hero-parallax-experimental'", m5, False))

# --- Adversarial mutation 6 (bonus): registryId not matching the section.* pattern ---
m6 = copy.deepcopy(example)
m6["nodes"][0]["registryId"] = "site-header"  # missing 'section.' prefix
results.append(check("adversarial: registryId missing 'section.' prefix", m6, False))

# --- Adversarial mutation 7 (bonus): fewer than minItems nodes (single-node page) ---
m7 = copy.deepcopy(example)
m7["nodes"] = [example["nodes"][0]]
results.append(check("adversarial: page with only 1 node (below minItems:2)", m7, False))

print()
total = len(results)
passed = sum(results)
print(f"{passed}/{total} checks behaved as expected")
sys.exit(0 if passed == total else 1)
