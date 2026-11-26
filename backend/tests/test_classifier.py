import pytest
from app.services.classifier import classify_category


@pytest.mark.parametrize(
    "title,text,expected",
    [
        # 1. English - Water
        (
            "Broken drinking water pipeline",
            "Water is leaking from the main pipe and tanker is needed urgently.",
            "water",
        ),
        # 2. Hinglish - Water (exact user scenario)
        (
            "Paani ki supply band hai",
            "Mere ghar ke paas pichle 3 din se paani nahi aa raha hai.",
            "water",
        ),
        # 3. Hindi (Devanagari) - Roads
        (
            "मुख्य सड़क पर बड़ा गड्ढा है",
            "रास्ता पूरी तरह खराब है और सड़क की मरम्मत की जरूरत है।",
            "roads",
        ),
        # 4. Hinglish - Electricity
        (
            "Bijli transformer kharab hai",
            "Raat se light nahi hai aur street light bhi band padi hai.",
            "electricity",
        ),
        # 5. English - Sanitation
        (
            "Overflowing sewage drain and garbage dump",
            "Trash has piled up near the clogged drain causing foul smell and mosquitoes.",
            "sanitation",
        ),
        # 6. Mixed Hindi + English - Health
        (
            "Hospital mein doctor aur dawai nahi hai",
            "Community clinic में dengue मरीजों के लिए ambulance और medicine नहीं मिल रही।",
            "health",
        ),
        # 7. Hinglish + Hindi - Police
        (
            "Market mein chori aur अवैध अतिक्रमण",
            "Raat ko patrolling aur suraksha badhane ke liye police madad chahiye.",
            "police",
        ),
        # 8. Mixed EN/HI - Roads vs other
        (
            "Massive pothole near flyover",
            "Footpath और सड़क पर गड्ढे की वजह से रोज जाम लगता है।",
            "roads",
        ),
        # 9. No match case
        (
            "Request for appointment schedule",
            "Please share the office visiting hours for document verification.",
            None,
        ),
    ],
)
def test_classify_category_cases(title, text, expected):
    assert classify_category(title, text) == expected


def test_auto_detect_sets_department_in_create_grievance(client):
    client.post("/api/v1/auth/otp/request", json={"phone": "9876543210"})
    token = client.post(
        "/api/v1/auth/otp/verify", json={"phone": "9876543210", "otp": "123456"}
    ).json()["access_token"]

    # Auto-detect (empty category) -> water
    resp = client.post(
        "/api/v1/grievances",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "title": "Paani ki supply band hai",
            "text": "Mere ghar ke paas pichle 3 din se paani nahi aa raha hai",
            "language": "hinglish",
            "is_anonymous": "false",
            "consent_accepted": "true",
        },
    )
    assert resp.status_code == 201
    g = resp.json()["grievance"]
    assert g["category"] == "water"
    assert g["dept_id"] is not None
    assert g["department"]["code"] == "water"
    assert g["department"]["name"] == "Water Supply & Jal Board"


def test_manual_category_overrides_auto_detect(client):
    client.post("/api/v1/auth/otp/request", json={"phone": "9876543210"})
    token = client.post(
        "/api/v1/auth/otp/verify", json={"phone": "9876543210", "otp": "123456"}
    ).json()["access_token"]

    resp = client.post(
        "/api/v1/grievances",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "title": "Paani ki supply band hai",
            "text": "Mere ghar ke paas paani nahi aa raha hai",
            "category": "general",
            "language": "hinglish",
            "is_anonymous": "false",
            "consent_accepted": "true",
        },
    )
    assert resp.status_code == 201
    g = resp.json()["grievance"]
    assert g["category"] == "general"
    assert g["department"]["code"] == "general"
