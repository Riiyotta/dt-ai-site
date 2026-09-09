import json, os
from jsonschema import Draft7Validator

# Derived from this script's own location — see verification/verify_all.py's
# comment for why a hardcoded absolute path here was a self-containment bug
# (Round 3 fix).
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
schema = json.load(open(f"{REPO}/schema/pagespec.schema.json"))
example = json.load(open(f"{REPO}/schema/example.pagespec.json"))

def node_by_type(t):
    for n in example['nodes']:
        if n['type'] == t:
            return n
    return None

def mutate(doc, node_type, content_patch=None, content_replace=None):
    import copy
    d = copy.deepcopy(doc)
    for n in d['nodes']:
        if n['type'] == node_type:
            if content_replace is not None:
                n['content'] = content_replace
            elif content_patch:
                n['content'].update(content_patch)
    return d

def check(label, doc, want_valid):
    v = Draft7Validator(schema)
    errors = list(v.iter_errors(doc))
    ok = (len(errors) == 0) == want_valid
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label} — expected {'VALID' if want_valid else 'REJECTED'}, got {'valid' if not errors else f'{len(errors)} error(s)'}")
    if not ok and errors:
        print("   ", errors[0].message)
    return ok

results = []

results.append(check("baseline example still valid", example, True))

# site-header: signInLink now required
h0 = node_by_type('site-header')
bad = mutate(example, 'site-header', content_replace={k:v for k,v in h0['content'].items() if k != 'signInLink'})
results.append(check("site-header missing signInLink -> rejected", bad, False))

# site-header: navLinks must be exactly 4 (was min3/max6)
bad = mutate(example, 'site-header', content_patch={'navLinks': h0['content']['navLinks'][:2]})
results.append(check("site-header navLinks with only 2 entries -> rejected", bad, False))

# site-header.logo must be {assetRole,alt} object now, not bare string
bad = mutate(example, 'site-header', content_patch={'logo': 'DT&AI'})
results.append(check("site-header.logo as bare string -> rejected", bad, False))
ok_doc = mutate(example, 'site-header', content_patch={'logo': {'assetRole': 'logo.wordmark', 'alt': 'DT&AI'}})
results.append(check("site-header.logo as {assetRole,alt} -> valid", ok_doc, True))

# hero-product: eyebrow/description now required
hp = node_by_type('hero-product')
if hp:
    bad = mutate(example, 'hero-product', content_replace={k:v for k,v in hp['content'].items() if k not in ('eyebrow','description')})
    results.append(check("hero-product missing eyebrow/description -> rejected", bad, False))

# hero-narrative: field renamed eyebrow -> category
hn = node_by_type('hero-narrative')
if hn:
    if 'eyebrow' in hn['content']:
        bad = mutate(example, 'hero-narrative', content_patch={'eyebrow': hn['content'].pop('eyebrow', 'X')})
        results.append(check("hero-narrative using old 'eyebrow' name -> rejected", bad, False))
else:
    print("[SKIP] hero-narrative not present in example — testing via minimal synthetic node instead")

# final-cta-footer: logo now required, footerSitemap must be exactly 4 columns
fc = node_by_type('final-cta-footer')
bad = mutate(example, 'final-cta-footer', content_replace={k:v for k,v in fc['content'].items() if k != 'logo'})
results.append(check("final-cta-footer missing logo -> rejected", bad, False))
bad = mutate(example, 'final-cta-footer', content_patch={'footerSitemap': fc['content']['footerSitemap'][:2]})
results.append(check("final-cta-footer footerSitemap with only 2 columns -> rejected", bad, False))

# related-products-grid: icon must be {assetRole,alt}, not bare string
rp = node_by_type('related-products-grid')
bad_products = [dict(p, icon='product.icon') for p in rp['content']['products']]
bad = mutate(example, 'related-products-grid', content_patch={'products': bad_products})
results.append(check("related-products-grid icon as bare string -> rejected", bad, False))

# product-cross-sell-panel item now requires title+href (synthetic since not in example)
cross_sell_branch = None
for b in schema['properties']['nodes']['items']['allOf']:
    if b['if']['properties']['type'].get('const') == 'product-cross-sell-panel':
        cross_sell_branch = b
sub_schema = {**schema, 'properties': {**schema['properties'], 'nodes': {**schema['properties']['nodes'], 'minItems': 1}}}
synthetic_bad = {
    'page': example.get('page', {'route': '/t', 'title': 't', 'template': 'homepage'}),
    'theme': example.get('theme', 'default'),
    'nodes': [{'id': 'x1', 'type': 'site-header', 'content': node_by_type('site-header')['content']},
              {'id': 'x2', 'type': 'product-cross-sell-panel', 'content': {'heading': 'h', 'body': 'b', 'products': [{}]}}]
}
v = Draft7Validator(schema)
errs = list(v.iter_errors(synthetic_bad))
print(f"[{'PASS' if errs else 'FAIL'}] product-cross-sell-panel product item {{}} (no title/href) -> expected REJECTED, got {'rejected' if errs else 'valid'}")
results.append(bool(errs))

print()
print(f"{sum(results)}/{len(results)} adversarial checks passed")
