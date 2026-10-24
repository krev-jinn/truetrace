import urllib.request
import json
import http.client
import os

# 1. Create investigation
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/investigations',
    data=json.dumps({'name': 'Test Upload Inv', 'description': 'testing upload'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
inv_data = json.loads(resp.read().decode())
inv_id = inv_data['id']
print('Created investigation:', inv_id)

# 2. Test JSON upload
json_file_path = os.path.abspath('demo_evidence/scenario_1_supported/host_events.json')
with open(json_file_path, 'rb') as f:
    json_bytes = f.read()

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="investigation_id"\r\n\r\n'
    f'{inv_id}\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="description"\r\n\r\n'
    f'test upload host\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="host_events.json"\r\n'
    f'Content-Type: application/json\r\n\r\n'
).encode('utf-8') + json_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

conn = http.client.HTTPConnection('127.0.0.1', 8000)
conn.request('POST', '/api/evidence/upload', body=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
res = conn.getresponse()
print('JSON Upload status:', res.status, res.reason)
print('JSON Upload response:', res.read().decode())

# 3. Test PCAP upload
pcap_file_path = os.path.abspath('demo_evidence/scenario_1_supported/capture.pcap')
with open(pcap_file_path, 'rb') as f:
    pcap_bytes = f.read()

body_pcap = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="investigation_id"\r\n\r\n'
    f'{inv_id}\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="description"\r\n\r\n'
    f'test upload pcap\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="capture.pcap"\r\n'
    f'Content-Type: application/vnd.tcpdump.pcap\r\n\r\n'
).encode('utf-8') + pcap_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

conn = http.client.HTTPConnection('127.0.0.1', 8000)
conn.request('POST', '/api/evidence/upload', body=body_pcap, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
res = conn.getresponse()
print('PCAP Upload status:', res.status, res.reason)
print('PCAP Upload response:', res.read().decode())
