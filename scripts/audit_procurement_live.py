import urllib.request
import json
import sys

payload = {
    'company': 'SolarInfra Tech India Pvt Ltd',
    'requirements': [
        {
            'category': 'Cables',
            'product_name': '1.1 kV XLPE insulated electrical cables',
            'specifications': {'voltage': '1.1 kV', 'insulation': 'XLPE'},
            'quantity': 1000,
            'unit': 'meters',
            'mandatory_standards': ['IS 7098 (Part 1)']
        },
        {
            'category': 'Solar PV',
            'product_name': 'Crystalline silicon terrestrial photovoltaic modules',
            'specifications': {'capacity': '540Wp', 'technology': 'Mono-PERC'},
            'quantity': 500,
            'unit': 'modules',
            'mandatory_standards': ['IS 14286']
        }
    ]
}

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/procurement/analyze',
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test_mock_token:usr_audit:buyer@solarinfra.in'
    }
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))

print('=== PROCUREMENT ANALYSIS RESPONSE VERIFICATION ===')
print('Status Code: 200 OK')
verdict = res.get('package_evaluation', {}).get('decision_summary', {}).get('verdict')
print('Package Evaluation Verdict:', verdict)
items = res.get('items', [])
print('Items Evaluated:', len(items))

for i, item in enumerate(items):
    req_item = item.get('requirement', {})
    eval_item = item.get('evaluation', {})
    retrieved = [s.get('is_code') for s in item.get('retrieved_standards', [])]
    p_name = req_item.get('product_name')
    cat = req_item.get('category')
    comp_status = eval_item.get('compliance_status')
    readiness = eval_item.get('composite_readiness_score')
    print(f'  Item {i+1}: {p_name} ({cat})')
    print(f'    Retrieved Standards: {retrieved}')
    print(f'    Compliance Status: {comp_status}')
    print(f'    Readiness Score: {readiness}')

sourcing = res.get('sourcing_recommendations', [])
print('Total Sourcing Recommendations:', len(sourcing))

region_only_count = 0
source_unit_count = 0
for s in sourcing:
    ptype = s.get('point_type')
    vstatus = s.get('verification_status')
    sname = s.get('source_name')
    suit = s.get('suitability_score')
    trust = s.get('trust_score')
    print(f'  Source: {sname} | point_type: {ptype} | status: {vstatus} | suitability: {suit} | trust: {trust}')
    if ptype == 'REGION_ONLY':
        region_only_count += 1
    elif ptype in ('SOURCE', 'MANUFACTURER', 'SUPPLIER'):
        source_unit_count += 1

print(f'Verified REGION_ONLY clusters count: {region_only_count}')
print(f'Verified Enterprise Source units count: {source_unit_count}')
assert region_only_count > 0, 'No REGION_ONLY sources returned!'
assert source_unit_count > 0, 'No Enterprise Source units returned!'
print('ALL PROCUREMENT REGRESSION ASSERTIONS PASSED.')
