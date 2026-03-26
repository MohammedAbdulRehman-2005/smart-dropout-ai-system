import requests
import json

def test_endpoints():
    print("Testing Smart EWS Endpoints...")
    
    # 1. Login
    res = requests.post("http://localhost:8000/auth/login", data={"username": "admin@school.edu", "password": "admin123"})
    if res.status_code != 200:
        print("Login failed:", res.text)
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # 2. Train model
    res = requests.post("http://localhost:8000/train-model", headers=headers)
    print("✅ Training:", res.json())
    
    # 3. Predict risk
    res = requests.post("http://localhost:8000/predict-risk", headers=headers, json={"student_id": 1})
    print("✅ Predict Risk:")
    print(json.dumps(res.json(), indent=2))
    
    # 4. Check Alerts
    res = requests.get("http://localhost:8000/alerts?unresolved_only=true", headers=headers)
    print("✅ Alerts:", len(res.json()["alerts"]))
    
if __name__ == "__main__":
    test_endpoints()
