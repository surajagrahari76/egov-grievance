import pytest
from app.services.classifier import classify_category, classify_department


@pytest.mark.parametrize(
    "title,text,expected",
    [
        (
            "Broken drinking water pipeline",
            "Water is leaking from the main pipe and tanker is needed urgently.",
            "water",
        ),
        (
            "Paani ki supply band hai",
            "Mere ghar ke paas pichle 3 din se paani nahi aa raha hai.",
            "water",
        ),
        (
            "मुख्य सड़क पर बड़ा गड्ढा है",
            "रास्ता पूरी तरह खराब है और सड़क की मरम्मत की जरूरत है।",
            "roads",
        ),
        (
            "Bijli transformer kharab hai",
            "Raat se light nahi hai aur street light bhi band padi hai.",
            "electricity",
        ),
        (
            "Overflowing sewage drain and garbage dump",
            "Trash has piled up near the clogged drain causing foul smell and mosquitoes.",
            "sanitation",
        ),
        (
            "Hospital mein doctor aur dawai nahi hai",
            "Community clinic में dengue मरीजों के लिए ambulance और medicine नहीं मिल रही।",
            "health",
        ),
        (
            "Market mein chori aur अवैध अतिक्रमण",
            "Raat ko patrolling aur suraksha badhane ke liye police madad chahiye.",
            "police",
        ),
        (
            "Request for appointment schedule",
            "Please share the office visiting hours for document verification.",
            None,
        ),
    ],
)
def test_classify_category_cases(title, text, expected):
    assert classify_category(title, text) == expected


@pytest.mark.parametrize(
    "text,expected_code",
    [
        ("Paani ki supply band hai", "water"),
        ("No water supply for 3 days", "water"),
        ("Sadak par bada gadda hai", "roads"),
        ("Bijli nahi aa rahi", "electricity"),
        ("Kachra nahi utha", "sanitation"),
        ("Hello random text", None),
    ],
)
def test_classify_department_db_lookup(db_session, text, expected_code):
    dept = classify_department(db_session, text)
    if expected_code is None:
        assert dept is None
    else:
        assert dept is not None
        assert dept.code == expected_code


def test_auto_detect_sets_department_and_general_fallback(client):
    client.post("/api/v1/auth/otp/request", json={"phone": "9876543210"})
    token = client.post(
        "/api/v1/auth/otp/verify", json={"phone": "9876543210", "otp": "123456"}
    ).json()["access_token"]

    # 1. Hinglish water -> Water Supply & Jal Board
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
    assert g["department"]["name"] == "Water Supply & Jal Board"

    # 2. Unmatched random text -> category="general", dept_id=None
    fallback_resp = client.post(
        "/api/v1/grievances",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "title": "Hello random text",
            "text": "Just testing unmatched complaint wording here.",
            "language": "en",
            "is_anonymous": "false",
            "consent_accepted": "true",
        },
    )
    assert fallback_resp.status_code == 201
    fg = fallback_resp.json()["grievance"]
    assert fg["category"] == "general"
    assert fg["dept_id"] is None


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
