"""
Round 3 addition — semantic/structural PageSpec validation.

JSON Schema (schema/pagespec.schema.json) can express per-node shape constraints
(required fields, item counts, enums, string patterns) but it CANNOT express
whole-document, order-dependent rules like "exactly one node of this type
across the array," "this type must come first/last," "these two types can
never both appear," or "type A may only be immediately followed by type B."
Those rules live in compatibility/graph.json instead — and Round 2's CHANGELOG
claimed a "full re-run of the templates-vs-graph rule check... 0 issues
remaining," but no persisted, re-runnable script implementing that check
existed anywhere in this repo (confirmed: grep for the rule names --
alwaysFirst/maxOnePerPage/canPrecede/etc. -- across every *.py file in the repo
returned zero hits before this file was added). That means the Round 2 audit
was a one-off manual pass with no regression protection: nothing would catch a
future template or example edit that violates the graph's own rules.

This module is that missing, persisted checker. It operates on an ordered
sequence of section typeIds (e.g. a PageSpec's `nodes[].type` list, or a
template's `nodes[].typeId` list) and evaluates every rule category in
compatibility/graph.json against it.
"""
import json, os, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_graph():
    return json.load(open(os.path.join(REPO, "compatibility", "graph.json")))


def check_sequence(seq, graph, label="sequence", template_category=None):
    """seq: ordered list of section typeId strings (repeats allowed in the list
    itself -- that's exactly what maxOnePerPage checks for).
    Returns a list of human-readable violation strings (empty == clean)."""
    issues = []
    rules = graph["rules"]
    adjacency = graph["adjacency"]
    rhythm = graph["rhythm"]

    if not seq:
        return [f"{label}: empty sequence"]

    # Normalize once: a template can legitimately serve more than one category tag
    # (e.g. long-form-page serves both 'changelog' and 'svb-update' routes).
    cats = []
    if template_category is not None:
        cats = list(template_category) if isinstance(template_category, (list, tuple, set)) else [template_category]

    # 1. alwaysFirst
    for t in rules.get("alwaysFirst", []):
        if t in seq and seq[0] != t:
            issues.append(f"{label}: '{t}' must be first (alwaysFirst) but sequence starts with '{seq[0]}'")
    if rules.get("alwaysFirst") and seq[0] not in rules["alwaysFirst"]:
        issues.append(f"{label}: first node is '{seq[0]}', expected one of alwaysFirst {rules['alwaysFirst']}")

    # 2. alwaysLast (with a documented exemption list, mirroring rhythm.heroRequiredUnless,
    # for the two templates README's "Known gaps" section explicitly says were measured
    # without a captured trailing footer boundary: protected-deposits-page, simple-page)
    exempt_last = rules.get("alwaysLastUnless", [])
    if rules.get("alwaysLast") and seq[-1] not in rules["alwaysLast"] and not any(c in exempt_last for c in cats):
        issues.append(f"{label}: last node is '{seq[-1]}', expected one of alwaysLast {rules['alwaysLast']}")

    # 3. mutuallyExclusive
    for pair in rules.get("mutuallyExclusive", []):
        present = [t for t in pair if t in seq]
        if len(present) > 1:
            issues.append(f"{label}: mutually exclusive types both present: {present}")

    # 4. heroTypes / heroMustFollowHeader / heroRequiredUnless
    hero_types = set(rules.get("heroTypes", []))
    heroes_present = [t for t in seq if t in hero_types]
    if rules.get("heroMustFollowHeader") and heroes_present:
        header = rules.get("alwaysFirst", [None])[0]
        if header in seq:
            header_idx = seq.index(header)
            hero_idx = seq.index(heroes_present[0])
            if hero_idx != header_idx + 1:
                issues.append(f"{label}: hero '{heroes_present[0]}' does not immediately follow '{header}' (heroMustFollowHeader)")
    if cats:
        exempt = rhythm.get("heroRequiredUnless", [])
        if not heroes_present and not any(c in exempt for c in cats):
            issues.append(f"{label}: no hero section present and template category '{cats}' is not in rhythm.heroRequiredUnless")

    # 5. maxOnePerPage
    for t in rules.get("maxOnePerPage", []):
        count = seq.count(t)
        if count > 1:
            issues.append(f"{label}: '{t}' appears {count} times but is maxOnePerPage")

    # 6. onlyOnHomepage / onlyOnChangelogOrSvbUpdateOrBlogPost / onlyOnBlogIndex
    # template_category may be a single string or a list of category tags (a single
    # template can legitimately serve more than one allowed category, e.g.
    # long-form-page serves both the 'changelog' and 'svb-update' routes).
    if cats:
        scoped_rules = {
            "onlyOnHomepage": ["homepage"],
            "onlyOnChangelogOrSvbUpdateOrBlogPost": ["changelog", "svb-update", "blog-post"],
            "onlyOnBlogIndex": ["blog-index"],
        }
        for rule_name, allowed_categories in scoped_rules.items():
            for t in rules.get(rule_name, []):
                if t in seq and not any(c in allowed_categories for c in cats):
                    issues.append(f"{label}: '{t}' is {rule_name} but template category is '{cats}'")

    # 7. adjacency.canPrecede (directional: seq[i] -> seq[i+1] must be an allowed successor)
    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i + 1]
        if a in adjacency and "canPrecede" in adjacency[a]:
            allowed = adjacency[a]["canPrecede"]
            if b not in allowed:
                issues.append(f"{label}: '{a}' -> '{b}' not allowed; '{a}'.canPrecede is {allowed}")

    # 8. rhythm.maxConsecutiveSameType
    max_consec = rhythm.get("maxConsecutiveSameType", {})
    run_type, run_len = None, 0
    for t in seq:
        if t == run_type:
            run_len += 1
        else:
            run_type, run_len = t, 1
        limit = max_consec.get(t)
        if limit is not None and run_len > limit:
            issues.append(f"{label}: '{t}' appears {run_len} times consecutively, exceeds maxConsecutiveSameType {limit}")

    # 9. rhythm.minSectionsPerPage
    min_sections = rhythm.get("minSectionsPerPage")
    if min_sections is not None and len(seq) < min_sections:
        issues.append(f"{label}: only {len(seq)} sections, below rhythm.minSectionsPerPage {min_sections}")

    return issues


# compatibility/graph.json itself is inconsistent about how it tags a template: some
# rules (rhythm.heroRequiredUnless) key off the *template id* ("long-form-page"),
# others (rules.onlyOnChangelogOrSvbUpdateOrBlogPost) key off a *route category*
# ("changelog"/"svb-update"/"blog-post") that doesn't 1:1 match any template id. Rather
# than silently picking one vocabulary, each template is tagged with every alias it's
# known by across the graph, so a rule written in either vocabulary resolves correctly.
TEMPLATE_CATEGORY = {
    "homepage": ["homepage"],
    "blog-index": ["blog-index"],
    "blog-post": ["blog-post"],
    "long-form-page": ["long-form-page", "changelog", "svb-update"],
    "protected-deposits-page": ["protected-deposits-page"],
    "simple-page": ["simple-page"],
    # everything else (product-page, campaign-product-page, narrative-landing-page,
    # realtime-page) has no special onlyOn*/heroRequiredUnless/alwaysLastUnless carve-out
}


def run():
    graph = load_graph()
    all_issues = []

    # (a) the shipped example PageSpec
    example = json.load(open(os.path.join(REPO, "schema", "example.pagespec.json")))
    seq = [n["type"] for n in example["nodes"]]
    all_issues += check_sequence(seq, graph, label="schema/example.pagespec.json", template_category=example.get("page", {}).get("template"))

    # (b) every template's declared node order
    for fp in sorted(glob.glob(os.path.join(REPO, "templates", "*.json"))):
        tid = os.path.splitext(os.path.basename(fp))[0]
        data = json.load(open(fp))
        seq = [n["typeId"] for n in data["nodes"]]
        category = TEMPLATE_CATEGORY.get(tid, tid)
        all_issues += check_sequence(seq, graph, label=f"templates/{os.path.basename(fp)}", template_category=category)

    return all_issues


if __name__ == "__main__":
    issues = run()
    print(f"[graph_rules_check] {len(issues)} issue(s)")
    for i in issues:
        print(" -", i)
    sys.exit(1 if issues else 0)
