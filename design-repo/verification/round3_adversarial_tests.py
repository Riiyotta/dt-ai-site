"""
Round 3 adversarial test suite.

Proves, with runnable code (not just prose), that the gaps found in this pass are
real and that the fixes close them:

  1. JSON Schema alone cannot catch a duplicated maxOnePerPage section, a missing
     alwaysFirst/alwaysLast section, or an illegal reordering -- but the new
     verification/graph_rules_check.py does.
  2. assetRole was previously an unconstrained string on every asset-ref field --
     now it's enum-constrained per field against assets/asset-roles.json's real
     roles, and a bogus role is rejected.
  3. x-maxWordsRoleBound was previously a schema annotation nobody enforced -- now
     verification/maxwords_check.py counts real words and catches an overlong string
     that a Draft7Validator pass alone would happily accept.
"""
import json, copy, os, sys
from jsonschema import Draft7Validator

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "verification"))
import graph_rules_check
import maxwords_check

schema = json.load(open(os.path.join(REPO, "schema", "pagespec.schema.json")))
example = json.load(open(os.path.join(REPO, "schema", "example.pagespec.json")))
graph = graph_rules_check.load_graph()

results = []


def check(label, ok):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    results.append(ok)
    return ok


# ---------------------------------------------------------------------------
# Category 2: semantic/structural validation JSON Schema cannot express
# ---------------------------------------------------------------------------

# 2a. Duplicate a maxOnePerPage section (customer-quote-panel appears once in the
# example; add a second copy). Schema alone must NOT catch this (proving the gap
# schema can't cover); graph_rules_check.py MUST catch it (proving the fix).
m1 = copy.deepcopy(example)
quote_node = next(n for n in m1["nodes"] if n["type"] == "customer-quote-panel")
dup_idx = m1["nodes"].index(quote_node)
m1["nodes"].insert(dup_idx, copy.deepcopy(quote_node))
schema_errors = list(Draft7Validator(schema).iter_errors(m1))
check(
    "duplicate maxOnePerPage section ('customer-quote-panel' x2): schema alone does NOT reject it (expected gap)",
    len(schema_errors) == 0,
)
seq1 = [n["type"] for n in m1["nodes"]]
graph_issues_1 = graph_rules_check.check_sequence(seq1, graph, label="mutation-1")
check(
    "duplicate maxOnePerPage section: graph_rules_check.py DOES reject it",
    any("maxOnePerPage" in i for i in graph_issues_1),
)

# 2b. Remove site-header (alwaysFirst) and the footer (alwaysLast). Schema alone
# must not catch it; graph_rules_check.py must.
m2 = copy.deepcopy(example)
m2["nodes"] = [n for n in m2["nodes"] if n["type"] not in ("site-header", "final-cta-footer")]
schema_errors = list(Draft7Validator(schema).iter_errors(m2))
check(
    "remove site-header + final-cta-footer: schema alone does NOT reject it (expected gap)",
    len(schema_errors) == 0,
)
seq2 = [n["type"] for n in m2["nodes"]]
graph_issues_2 = graph_rules_check.check_sequence(seq2, graph, label="mutation-2", template_category=example["page"]["template"])
check(
    "remove site-header + final-cta-footer: graph_rules_check.py catches BOTH the missing alwaysFirst and missing alwaysLast",
    any("alwaysFirst" in i or "first node" in i for i in graph_issues_2) and any("alwaysLast" in i or "last node" in i for i in graph_issues_2),
)

# 2c. Reorder two sections so an adjacency.canPrecede rule is violated: swap
# related-products-grid and final-cta-footer so the footer is no longer last and
# related-products-grid no longer precedes it (related-products-grid.canPrecede is
# only ["final-cta-footer"]).
m3 = copy.deepcopy(example)
types = [n["type"] for n in m3["nodes"]]
i_rpg, i_footer = types.index("related-products-grid"), types.index("final-cta-footer")
m3["nodes"][i_rpg], m3["nodes"][i_footer] = m3["nodes"][i_footer], m3["nodes"][i_rpg]
schema_errors = list(Draft7Validator(schema).iter_errors(m3))
check(
    "reorder related-products-grid <-> final-cta-footer: schema alone does NOT reject it (expected gap)",
    len(schema_errors) == 0,
)
seq3 = [n["type"] for n in m3["nodes"]]
graph_issues_3 = graph_rules_check.check_sequence(seq3, graph, label="mutation-3", template_category=example["page"]["template"])
check(
    "reorder related-products-grid <-> final-cta-footer: graph_rules_check.py catches the adjacency/alwaysLast violation",
    len(graph_issues_3) > 0,
)

# 2d. Baseline: the real, unmodified example must be clean under the new checker too.
seq0 = [n["type"] for n in example["nodes"]]
graph_issues_0 = graph_rules_check.check_sequence(seq0, graph, label="baseline", template_category=example["page"]["template"])
check("baseline example.pagespec.json: graph_rules_check.py reports 0 issues", len(graph_issues_0) == 0)

# ---------------------------------------------------------------------------
# Category 3: assetRole escape hatch
# ---------------------------------------------------------------------------

m4 = copy.deepcopy(example)
for n in m4["nodes"]:
    if n["type"] == "site-header":
        n["content"]["logo"]["assetRole"] = "totally-made-up-role"
check(
    "site-header.logo.assetRole = made-up string -> schema now REJECTS it (enum added, Round 3)",
    len(list(Draft7Validator(schema).iter_errors(m4))) > 0,
)

m5 = copy.deepcopy(example)
for n in m5["nodes"]:
    if n["type"] == "hero-product":
        n["content"]["heroVisual"]["assetRole"] = "customer.logo"  # wrong role for this field
check(
    "hero-product.heroVisual.assetRole = a real-but-wrong-for-this-field role ('customer.logo') -> schema REJECTS it",
    len(list(Draft7Validator(schema).iter_errors(m5))) > 0,
)

m6 = copy.deepcopy(example)
for n in m6["nodes"]:
    if n["type"] == "hero-product":
        n["content"]["heroVisual"]["assetRole"] = "hero.illustration"  # correct role
check(
    "hero-product.heroVisual.assetRole = the correct role ('hero.illustration') -> still valid",
    len(list(Draft7Validator(schema).iter_errors(m6))) == 0,
)

# Phantom field removal: hero-simple/hero-home no longer accept heroVisual/eyebrow
# (no basis in their contentModel or componentRefs -- see CHANGELOG).
synthetic_hero_simple = {
    "page": {"route": "/t/", "title": "t", "template": "simple-page"},
    "theme": "dtai-light",
    "nodes": [
        {"type": "site-header", "registryId": "section.site-header", "content": example["nodes"][0]["content"]},
        {
            "type": "hero-simple",
            "registryId": "section.hero-simple",
            "content": {"headline": "A short institutional headline", "heroVisual": {"assetRole": "hero.illustration", "alt": "x"}},
        },
    ],
}
check(
    "hero-simple.heroVisual (phantom field, Round 3 removed) -> schema now rejects extra property",
    len(list(Draft7Validator(schema).iter_errors(synthetic_hero_simple))) > 0,
)

# ---------------------------------------------------------------------------
# Category 6: maxWords runtime enforcement
# ---------------------------------------------------------------------------

m7 = copy.deepcopy(example)
for n in m7["nodes"]:
    if n["type"] == "hero-product":
        # x-maxWordsRoleBound for hero-product.headline is 12; blow way past it.
        n["content"]["headline"] = " ".join(["word"] * 30)
schema_errors = list(Draft7Validator(schema).iter_errors(m7))
check(
    "hero-product.headline blown past x-maxWordsRoleBound(12) with 30 words: schema alone does NOT reject it (expected gap -- 'x-' keywords are annotations only)",
    len(schema_errors) == 0,
)
mw_issues = maxwords_check.check_document(m7, schema, label="mutation-7")
check(
    "same over-length headline: maxwords_check.py DOES catch it",
    any("headline" in i for i in mw_issues),
)

mw_issues_baseline = maxwords_check.check_document(example, schema, label="baseline")
check("baseline example.pagespec.json: maxwords_check.py reports 0 violations", len(mw_issues_baseline) == 0)

print()
print(f"{sum(results)}/{len(results)} Round 3 adversarial checks passed")
sys.exit(0 if all(results) else 1)
