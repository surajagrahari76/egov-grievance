def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db_dialect"] == "sqlite"


def test_citizen_otp_login_and_profile(client):
    req = client.post("/api/v1/auth/otp/request", json={"phone": "9876543210"})
    assert req.status_code == 200
    assert "Demo OTP: 123456" in req.json()["mock_otp_hint"]

    verify = client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": "9876543210", "otp": "123456", "consent_accepted": True},
    )
    assert verify.status_code == 200
    body = verify.json()
    assert body["user"]["role"] == "citizen"
    token = body["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["phone"] == "9876543210"


def test_rbac_blocks_citizen_from_staff_endpoint(client):
    client.post("/api/v1/auth/otp/request", json={"phone": "9876543210"})
    citizen_token = client.post(
        "/api/v1/auth/otp/verify", json={"phone": "9876543210", "otp": "123456"}
    ).json()["access_token"]

    blocked = client.get(
        "/api/v1/grievances/rbac-check/staff-only",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert blocked.status_code == 403

    officer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "officer.water@demo.gov.in", "password": "Officer123!"},
    )
    assert officer_login.status_code == 200
    officer_token = officer_login.json()["access_token"]
    allowed = client.get(
        "/api/v1/grievances/rbac-check/staff-only",
        headers={"Authorization": f"Bearer {officer_token}"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["role"] == "officer"


def test_submit_and_list_citizen_grievance_with_attachment(client):
    client.post("/api/v1/auth/otp/request", json={"phone": "9876543210"})
    token = client.post(
        "/api/v1/auth/otp/verify", json={"phone": "9876543210", "otp": "123456"}
    ).json()["access_token"]

    resp = client.post(
        "/api/v1/grievances",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "title": "Water pipeline leakage on Main Avenue",
            "text": "Clean drinking water is overflowing from the main valve near house 42.",
            "category": "water",
            "language": "en",
            "address": "42 Main Avenue, Connaught Place",
            "ward_id": "1",
            "is_anonymous": "false",
            "consent_accepted": "true",
        },
        files={"files": ("leak.png", b"\x89PNG\r\n\x1a\nfake-png-bytes", "image/png")},
    )
    assert resp.status_code == 201
    created = resp.json()["grievance"]
    assert created["ticket_id"].startswith("GRV-")
    assert len(created["attachments"]) == 1
    assert created["status"] == "submitted"

    mine = client.get("/api/v1/grievances/mine", headers={"Authorization": f"Bearer {token}"})
    assert mine.status_code == 200
    tickets = [item["ticket_id"] for item in mine.json()["items"]]
    assert created["ticket_id"] in tickets


def test_anonymous_grievance_and_public_tracking(client):
    resp = client.post(
        "/api/v1/grievances",
        data={
            "title": "Broken sewage drain near school",
            "text": "Open sewage drain outside government primary school is overflowing.",
            "category": "sanitation",
            "language": "en",
            "ward_id": "2",
            "is_anonymous": "true",
            "consent_accepted": "true",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    ticket_id = data["grievance"]["ticket_id"]
    anon_code = data["anonymous_tracking_code"]
    assert anon_code.startswith("ANON-")

    bad_track = client.get(f"/api/v1/grievances/track/{ticket_id}?anonymous_code=ANON-WRONG")
    assert bad_track.status_code == 403

    ok_track = client.get(f"/api/v1/grievances/track/{ticket_id}?anonymous_code={anon_code}")
    assert ok_track.status_code == 200
    assert ok_track.json()["ticket_id"] == ticket_id
