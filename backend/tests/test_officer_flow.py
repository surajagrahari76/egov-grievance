def _get_citizen_token(client) -> str:
    client.post("/api/v1/auth/otp/request", json={"phone": "9876543210"})
    resp = client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": "9876543210", "otp": "123456", "consent_accepted": True},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _get_staff_token(client, email: str = "district@demo.gov.in", password: str = "Officer123!") -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_staff_status_workflow_end_to_end_and_notifications(client):
    citizen_tok = _get_citizen_token(client)
    staff_tok = _get_staff_token(client, "district@demo.gov.in", "Officer123!")

    # Citizen creates a water grievance
    create_resp = client.post(
        "/api/v1/grievances",
        headers={"Authorization": f"Bearer {citizen_tok}"},
        data={
            "title": "Paani ki supply band hai",
            "text": "Water supply has stopped in our block since morning.",
            "language": "hinglish",
            "is_anonymous": "false",
            "consent_accepted": "true",
        },
    )
    assert create_resp.status_code == 201
    ticket_id = create_resp.json()["grievance"]["ticket_id"]
    assert create_resp.json()["grievance"]["status"] == "submitted"

    # Staff lists queue and finds ticket
    queue_resp = client.get(
        "/api/v1/officer/grievances",
        headers={"Authorization": f"Bearer {staff_tok}"},
    )
    assert queue_resp.status_code == 200
    assert any(item["ticket_id"] == ticket_id for item in queue_resp.json()["items"])

    # Step-by-step transitions: submitted -> assigned -> in_progress -> resolved -> closed
    steps = [
        ("assigned", "Assigned to ward water engineer"),
        ("in_progress", "Field team dispatched for valve inspection"),
        ("resolved", "Main supply valve repaired and water restored"),
        ("closed", "Citizen confirmation received, closing ticket"),
    ]
    for next_status, remarks in steps:
        upd = client.patch(
            f"/api/v1/officer/grievances/{ticket_id}/status",
            headers={"Authorization": f"Bearer {staff_tok}"},
            json={"status": next_status, "remarks": remarks},
        )
        assert upd.status_code == 200
        assert upd.json()["status"] == next_status

        # Citizen verifies via public /track and /mine
        track = client.get(f"/api/v1/grievances/track/{ticket_id}")
        assert track.status_code == 200
        track_data = track.json()
        assert track_data["status"] == next_status
        assert any(
            h["to_status"] == next_status and h["remarks"] == remarks
            for h in track_data["status_history"]
        )

    mine = client.get("/api/v1/grievances/mine", headers={"Authorization": f"Bearer {citizen_tok}"})
    assert mine.status_code == 200
    matched = [g for g in mine.json()["items"] if g["ticket_id"] == ticket_id][0]
    assert matched["status"] == "closed"
    assert matched["resolved_at"] is not None
    assert matched["closed_at"] is not None

    # Citizen receives in-app notifications for each status update
    notifs = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {citizen_tok}"})
    assert notifs.status_code == 200
    assert len(notifs.json()) >= 4

    first_id = notifs.json()[0]["id"]
    mark_read = client.patch(
        f"/api/v1/notifications/{first_id}/read",
        headers={"Authorization": f"Bearer {citizen_tok}"},
    )
    assert mark_read.status_code == 200
    assert mark_read.json()["is_read"] is True


def test_department_scoping_and_reassign(client):
    water_officer_tok = _get_staff_token(client, "officer.water@demo.gov.in", "Officer123!")
    district_tok = _get_staff_token(client, "district@demo.gov.in", "Officer123!")

    # Water officer cannot update a Roads ticket (GRV-2026-100002 is Roads in seed.py)
    forbidden = client.patch(
        "/api/v1/officer/grievances/GRV-2026-100002/status",
        headers={"Authorization": f"Bearer {water_officer_tok}"},
        json={"status": "in_progress", "remarks": "Trying cross-dept update"},
    )
    assert forbidden.status_code == 403

    # District head reassigns GRV-2026-100002 to sanitation
    reassign = client.post(
        "/api/v1/officer/grievances/GRV-2026-100002/reassign",
        headers={"Authorization": f"Bearer {district_tok}"},
        json={"dept_code": "sanitation", "remarks": "Drain blockage is root cause"},
    )
    assert reassign.status_code == 200
    assert reassign.json()["category"] == "sanitation"
    assert reassign.json()["department"]["code"] == "sanitation"


def test_staff_and_input_edge_cases(client):
    citizen_tok = _get_citizen_token(client)
    staff_tok = _get_staff_token(client, "district@demo.gov.in", "Officer123!")

    # 1. Citizen calling staff endpoint -> 403
    assert (
        client.get(
            "/api/v1/officer/grievances",
            headers={"Authorization": f"Bearer {citizen_tok}"},
        ).status_code
        == 403
    )

    # 2. Unauthenticated calling staff endpoint -> 401
    assert client.get("/api/v1/officer/grievances").status_code == 401

    # 3. Invalid status value -> 422
    assert (
        client.patch(
            "/api/v1/officer/grievances/GRV-2026-100001/status",
            headers={"Authorization": f"Bearer {staff_tok}"},
            json={"status": "not_a_real_status"},
        ).status_code
        == 422
    )

    # 4. Invalid ticket number -> 404
    assert (
        client.patch(
            "/api/v1/officer/grievances/GRV-9999-000000/status",
            headers={"Authorization": f"Bearer {staff_tok}"},
            json={"status": "resolved"},
        ).status_code
        == 404
    )

    # 5. Wrong OTP -> 401
    client.post("/api/v1/auth/otp/request", json={"phone": "9876543210"})
    wrong_otp = client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": "9876543210", "otp": "000000", "consent_accepted": True},
    )
    assert wrong_otp.status_code == 401

    # 6. Empty form submission -> 422
    empty_submit = client.post(
        "/api/v1/grievances",
        headers={"Authorization": f"Bearer {citizen_tok}"},
        data={},
    )
    assert empty_submit.status_code == 422
