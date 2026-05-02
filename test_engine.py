import urllib.request
import json

payload = json.dumps({
    "equation": "x'' + 0.2*x' + x = cos(t)",
    "ic": {"x": 1.0, "dx": 0.0},
    "time_span": [0, 50]
}).encode()

req = urllib.request.Request(
    "http://localhost:8000/generate-solver",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    r = urllib.request.urlopen(req, timeout=10)
    data = json.loads(r.read().decode())
    print("SUCCESS!")
    print("is_valid     :", data["is_valid"])
    print("method_chosen:", data["method_chosen"])
    print("debug_notes  :", data["debug_notes"])
    print("issues_found :", data["issues_found"])
    print()
    print("--- First 600 chars of full_code ---")
    print(data["full_code"][:600])
except Exception as e:
    print("FAILED:", e)
