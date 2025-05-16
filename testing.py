import requests

# === CONFIGURATION ===
API_BASE = "http://localhost:8000"
EMAIL = "legendtest123@gmail.com"  # <-- replace with valid test user
PASSWORD = "testpass123"  # <-- replace with correct password


# === STEP 1: Authenticate ===
def get_token():
    url = f"{API_BASE}/auth/login"
    response = requests.post(url, json={"email": EMAIL, "password": PASSWORD})
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Authenticated")
        return token
    else:
        print("❌ Login failed:", response.text)
        return None


# === STEP 2: Send chat message ===
def test_chat(token, message="How do I apply?"):
    url = f"{API_BASE}/chat"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "message": message,
        "chat_id": None,
        "model": "openai",
        "temperature": 0.7,
        "active_pdf_type": "default",
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()

        print("\n🧠 Bot Response:")
        print(data["response"])

        rule_based = data.get("followups", {}).get("rule_based", [])
        ai_generated = data.get("followups", {}).get("ai_generated", [])

        print("\n💡 Followup Suggestions:")
        print("Rule-Based:", rule_based)
        print("AI-Generated:", ai_generated)

        # Optionally print individual followups if needed
        if ai_generated:
            print("\n🤖 AI Follow-up 1:", ai_generated[0])
            if len(ai_generated) > 1:
                print("🤖 AI Follow-up 2:", ai_generated[1])

    else:
        print("❌ Chat failed:", response.status_code, response.text)


# === RUN TEST ===
if __name__ == "__main__":
    token = get_token()
    if token:
        test_chat(token)
