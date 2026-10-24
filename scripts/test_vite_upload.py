import http.client
import os

pcap_file_path = os.path.abspath('demo_evidence/scenario_1_supported/capture.pcap')
with open(pcap_file_path, 'rb') as f:
    pcap_bytes = f.read()

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="investigation_id"\r\n\r\n'
    f'inv-fff0a989\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="description"\r\n\r\n'
    f'test upload pcap via vite proxy\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="capture.pcap"\r\n'
    f'Content-Type: application/vnd.tcpdump.pcap\r\n\r\n'
).encode('utf-8') + pcap_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

conn = http.client.HTTPConnection('127.0.0.1', 5173)
conn.request('POST', '/api/evidence/upload', body=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
res = conn.getresponse()
print('PCAP Upload via Vite (5173) status:', res.status, res.reason)
print('Response:', res.read().decode())
