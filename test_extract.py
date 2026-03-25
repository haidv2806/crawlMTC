import requests, re

url = 'https://metruyenchu.co/truyen/toan-cau-than-tuyen-bat-dau-lua-chon-phong-do-dai-de'
headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }
html = requests.get(url, headers=headers).text

print("bookId:")
print(re.findall(r'"bookId":"?([^"}]+)"?', html)[:5])
print("id:")
print(re.findall(r'"id":"?([^"}]+)"?', html)[:5])
print("_id:")
print(re.findall(r'"_id":"?([^"}]+)"?', html)[:5])

