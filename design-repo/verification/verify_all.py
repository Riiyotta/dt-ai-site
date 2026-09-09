import json, os, glob, re, sys

# REPO is derived from this script's own location, never hardcoded, so that this
# check is self-contained: running it from an extracted zip / a different checkout
# / a different machine validates the files actually present there, not whatever
# happens to live at one engineer's original absolute path. (Round 3 fix — see
# CHANGELOG.md; a hardcoded absolute path here previously caused the script to
# silently re-validate the ORIGINAL repo even when run from an isolated copy,
# reporting "ALL CHECKS CLEAN" regardless of what was actually in that copy.)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
issues = []

def load_json(path):
    with open(path) as f:
        return json.load(f)

# ---------- 1. every *.json parses ----------
all_json = sorted(glob.glob(os.path.join(REPO, "**/*.json"), recursive=True))
parsed = {}
for fp in all_json:
    try:
        parsed[fp] = load_json(fp)
    except Exception as e:
        issues.append(f"PARSE ERROR: {fp}: {e}")
print(f"[1] JSON parse check: {len(all_json)} files, {len(all_json)-len([i for i in issues if 'PARSE ERROR' in i])} ok")

# ---------- registry: collect every registryId / typeId / id from primitives, components, sections, templates ----------
registry_ids = set()
type_ids = set()
for kind_dir in ["primitives", "components", "sections", "templates"]:
    for fp in glob.glob(os.path.join(REPO, kind_dir, "*.json")):
        data = parsed.get(fp)
        if not data:
            continue
        rid = data.get("registryId") or data.get("id")
        if rid:
            registry_ids.add(rid)
        if "typeId" in data:
            type_ids.add(data["typeId"])
        # primitives use bare filename ids too, e.g. "Text"
        if kind_dir == "primitives" and "id" in data:
            registry_ids.add(data["id"])

# ---------- 2. every ref/extends/composedOf/itemRef resolves ----------
REF_KEY_PATTERN = re.compile(r"^(ref|extends|composedOf|itemRef|componentRefs)$")

def walk_refs(obj, path, fp):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("componentRefs",) and isinstance(v, list):
                for item in v:
                    check_component_ref(item, fp)
            elif k in ("ref", "extends", "itemRef") and isinstance(v, str):
                check_dotted_ref(v, fp)
            elif k == "composedOf" and isinstance(v, list):
                for item in v:
                    check_component_ref(item, fp)
            elif k == "tokenRefs" and isinstance(v, list):
                for item in v:
                    if isinstance(item, str) and item.startswith("tokens."):
                        check_dotted_ref(item, fp)
            else:
                walk_refs(v, path + [k], fp)
    elif isinstance(obj, list):
        for item in obj:
            walk_refs(item, path, fp)

def check_component_ref(item, fp):
    # e.g. "primitives/Text.json" or "primitives/Text" or "components/footer.json"
    if not isinstance(item, str):
        return
    norm = item[:-5] if item.endswith(".json") else item
    candidate = os.path.join(REPO, norm + ".json")
    if not os.path.exists(candidate):
        issues.append(f"DANGLING componentRef in {os.path.relpath(fp, REPO)}: '{item}' -> no file at {os.path.relpath(candidate, REPO)}")

def check_dotted_ref(v, fp):
    # e.g. "tokens.10-semantic.color-roles.roles.text.body" or "primitives/Text.json"
    if v.startswith("tokens."):
        parts = v.split(".")
        # tokens.<layer>.<file>...
        if len(parts) < 3:
            issues.append(f"MALFORMED token ref in {os.path.relpath(fp, REPO)}: '{v}'")
            return
        layer, filename = parts[1], parts[2]
        candidate = os.path.join(REPO, "tokens", layer, filename + ".json")
        if not os.path.exists(candidate):
            issues.append(f"DANGLING token ref in {os.path.relpath(fp, REPO)}: '{v}' -> no file at tokens/{layer}/{filename}.json")
    elif "/" in v:
        check_component_ref(v, fp)

for fp in all_json:
    data = parsed.get(fp)
    if data is not None:
        walk_refs(data, [], fp)

n_ref_issues = len([i for i in issues if "DANGLING" in i or "MALFORMED" in i])
print(f"[2] ref/extends/composedOf/componentRef resolution: {n_ref_issues} dangling")

# ---------- 3. allowlist <-> registry parity ----------
allowlist = load_json(os.path.join(REPO, "tokens/llm/component-allowlist.json"))
allowed = set(allowlist["allowed"])
missing_from_allowlist = registry_ids - allowed
missing_from_registry = allowed - registry_ids
if missing_from_allowlist:
    issues.append(f"ALLOWLIST PARITY: registry entries missing from allowlist: {sorted(missing_from_allowlist)}")
if missing_from_registry:
    issues.append(f"ALLOWLIST PARITY: allowlisted ids with no registry entry: {sorted(missing_from_registry)}")
print(f"[3] allowlist<->registry parity: {len(missing_from_allowlist)} missing-from-allowlist, {len(missing_from_registry)} missing-from-registry")

# ---------- 4. maxWords vs typography role ceiling ----------
typo_roles = load_json(os.path.join(REPO, "tokens/10-semantic/typography-roles.json"))["roles"]
role_ceiling = {name: r["maxWords"] for name, r in typo_roles.items()}
# For each section, check contentModel maxWords vs any typography role it's bound to isn't directly
# machine-checkable without a role<->field binding table; instead verify no section constraint maxWords
# value exceeds the widest available role ceiling group it plausibly maps to (heading/body/label/code tiers).
tiers = {
    "heading": max(v for k, v in role_ceiling.items() if k.startswith("heading") or k.startswith("display")),
    "body": max(v for k, v in role_ceiling.items() if k.startswith("body")),
    "label": max(v for k, v in role_ceiling.items() if k.startswith("label")),
    "code": max(v for k, v in role_ceiling.items() if k.startswith("code")),
}
maxwords_violations = []
for fp in glob.glob(os.path.join(REPO, "sections", "*.json")):
    data = parsed[fp]
    mw = data.get("constraints", {}).get("maxWords", {})
    for field, val in mw.items():
        if not isinstance(val, int):
            continue
        fl = field.lower()
        if "head" in fl or "title" in fl:
            ceiling = tiers["heading"]
        elif "body" in fl or "desc" in fl or "answer" in fl:
            ceiling = tiers["body"]
        elif "code" in fl:
            ceiling = tiers["code"]
        else:
            ceiling = tiers["label"]
        if val > ceiling:
            maxwords_violations.append(f"{os.path.relpath(fp, REPO)}: constraints.maxWords.{field}={val} exceeds widest {('heading' if ceiling==tiers['heading'] else 'body' if ceiling==tiers['body'] else 'label')} role ceiling ({ceiling})")
issues.extend(maxwords_violations)
print(f"[4] maxWords vs typography-role ceiling: {len(maxwords_violations)} violations")

# ---------- 5. every template/compatibility-graph section reference resolves to a real typeId ----------
section_type_ids = set()
for fp in glob.glob(os.path.join(REPO, "sections", "*.json")):
    section_type_ids.add(parsed[fp]["typeId"])

phantom = []
for fp in glob.glob(os.path.join(REPO, "templates", "*.json")):
    data = parsed[fp]
    for node in data.get("nodes", []):
        if node["typeId"] not in section_type_ids:
            phantom.append(f"{os.path.relpath(fp, REPO)}: node typeId '{node['typeId']}' has no sections/*.json entry")

graph = load_json(os.path.join(REPO, "compatibility/graph.json"))
graph_type_refs = set()
# alwaysLastUnless (Round 3) holds *template ids*, not section typeIds -- it's an
# exemption list for the alwaysLast rule (see verification/graph_rules_check.py),
# so it's excluded from this section-typeId resolution check the same way
# rhythm.heroRequiredUnless (also template ids) already is by living outside "rules".
TYPEID_EXEMPT_RULE_KEYS = {"alwaysLastUnless"}
for rule_key, rule_list in graph["rules"].items():
    if rule_key in TYPEID_EXEMPT_RULE_KEYS:
        continue
    if isinstance(rule_list, list):
        for item in rule_list:
            if isinstance(item, list):
                graph_type_refs.update(item)
            elif isinstance(item, str):
                graph_type_refs.add(item)
graph_type_refs.update(graph["adjacency"].keys())
for k, v in graph["adjacency"].items():
    for lst in v.values():
        graph_type_refs.update(lst)
for t in graph_type_refs:
    if t not in section_type_ids:
        phantom.append(f"compatibility/graph.json: references phantom typeId '{t}'")

issues.extend(phantom)
print(f"[5] template/compat-graph -> section typeId resolution: {len(phantom)} phantom references")

# ---------- 6. compatibility/graph.json semantic/order rules (Round 3) ----------
# JSON Schema can't express "exactly one of this type in the array," "type A must
# come first/last," "these two are mutually exclusive," or "A may only be followed
# by B" -- those live in compatibility/graph.json and were previously enforced only
# by a one-off manual audit (Round 2's CHANGELOG entry), with no persisted script.
# See verification/graph_rules_check.py.
import graph_rules_check
graph_issues = graph_rules_check.run()
issues.extend(f"GRAPH RULE: {i}" for i in graph_issues)
print(f"[6] compatibility/graph.json rule enforcement (alwaysFirst/alwaysLast/mutuallyExclusive/heroTypes/maxOnePerPage/onlyOnX/adjacency/rhythm): {len(graph_issues)} violations")

# ---------- 7. maxWords runtime enforcement against real content (Round 3) ----------
# x-maxWordsRoleBound in schema/pagespec.schema.json is a plain JSON Schema
# annotation -- standard validators (including this repo's own Draft7Validator
# usage) never enforce a non-standard "x-" keyword. Before this check, NOTHING in
# the repo counted words in an actual content string against its declared bound,
# not even the bundled example. See verification/maxwords_check.py.
import maxwords_check
maxwords_issues = maxwords_check.run()
issues.extend(f"MAXWORDS: {i}" for i in maxwords_issues)
print(f"[7] maxWords runtime enforcement against schema/example.pagespec.json content: {len(maxwords_issues)} violations")

print()
if issues:
    print(f"=== {len(issues)} ISSUE(S) FOUND ===")
    for i in issues:
        print(" -", i)
    sys.exit(1)
else:
    print("=== ALL CHECKS CLEAN ===")
    sys.exit(0)
