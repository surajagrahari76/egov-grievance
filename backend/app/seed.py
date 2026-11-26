from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.security import hash_password, hash_token
from app.models.grievance import Grievance, StatusHistory
from app.models.organization import Department, Officer, Ward
from app.models.governance import SLARule
from app.models.user import User


DEPARTMENTS = [
    ("water", "Water Supply & Jal Board", "जल आपूर्ति विभाग", "1916"),
    ("electricity", "Electricity & Power Distribution", "विद्युत विभाग", "1912"),
    ("roads", "Roads & Public Works (PWD)", "सड़क एवं लोक निर्माण विभाग", "1800-11-2201"),
    ("sanitation", "Sanitation & Solid Waste", "स्वच्छता एवं कचरा प्रबंधन", "1533"),
    ("health", "Public Health & Hospitals", "स्वास्थ्य विभाग", "104"),
    ("police", "Law & Order / Municipal Safety", "पुलिस एवं सुरक्षा", "112"),
    ("general", "General Municipal Administration", "सामान्य प्रशासन", "1800-11-0001"),
]

WARDS = [
    ("W-01", "Connaught Place", "Central", "New Delhi", 28.6315, 77.2167),
    ("W-02", "Karol Bagh", "Central", "New Delhi", 28.6519, 77.1909),
    ("W-03", "Rohini Sector 7", "North", "New Delhi", 28.7041, 77.1025),
    ("W-04", "Dwarka Sector 10", "West", "New Delhi", 28.5823, 77.0500),
    ("W-05", "Lajpat Nagar", "South", "New Delhi", 28.5677, 77.2433),
    ("W-06", "Mayur Vihar Phase 1", "East", "New Delhi", 28.6090, 77.2945),
]


def seed_database(db: Session) -> None:
    """Idempotent seed script for Phase 1 core entities and demo accounts."""
    now = datetime.now(timezone.utc)

    dept_map: dict[str, Department] = {}
    for code, name, name_hi, helpline in DEPARTMENTS:
        dept = db.query(Department).filter(Department.code == code).first()
        if not dept:
            dept = Department(code=code, name=name, name_hi=name_hi, helpline=helpline, is_active=True)
            db.add(dept)
            db.flush()
        dept_map[code] = dept

    ward_map: dict[str, Ward] = {}
    for code, name, zone, city, lat, lng in WARDS:
        ward = db.query(Ward).filter(Ward.code == code).first()
        if not ward:
            ward = Ward(code=code, name=name, zone=zone, city=city, center_lat=lat, center_lng=lng)
            db.add(ward)
            db.flush()
        ward_map[code] = ward

    # Default SLA rules
    sla_defaults = [
        ("critical", 4),
        ("high", 24),
        ("medium", 48),
        ("low", 96),
    ]
    for prio, hours in sla_defaults:
        exists = (
            db.query(SLARule)
            .filter(SLARule.dept_id.is_(None), SLARule.category == "default", SLARule.priority == prio)
            .first()
        )
        if not exists:
            db.add(SLARule(dept_id=None, category="default", priority=prio, resolution_hours=hours, is_active=True))

    # Demo Citizen
    citizen = db.query(User).filter(User.phone == "9876543210").first()
    if not citizen:
        citizen = User(
            name="Aarav Sharma",
            phone="9876543210",
            email="citizen@demo.gov.in",
            role="citizen",
            preferred_lang="en",
            consent_accepted_at=now,
            is_active=True,
        )
        db.add(citizen)
        db.flush()

    # Staff accounts across RBAC hierarchy
    staff_specs = [
        ("admin@demo.gov.in", "Admin123!", "Meera Nair", "admin", None, None, None, "Chief System Administrator"),
        ("district@demo.gov.in", "Officer123!", "Rajesh Verma", "district_head", "general", None, "district_head", "District Magistrate Nodal"),
        ("depthead.water@demo.gov.in", "Officer123!", "Sunita Kulkarni", "dept_head", "water", None, "dept_head", "Chief Engineer - Water"),
        ("officer.water@demo.gov.in", "Officer123!", "Vikram Singh", "officer", "water", "W-01", "officer", "Junior Engineer - Water (W-01)"),
        ("officer.roads@demo.gov.in", "Officer123!", "Priya Menon", "officer", "roads", "W-02", "officer", "Assistant Engineer - Roads (W-02)"),
    ]

    officer_by_email: dict[str, Officer] = {}
    for email, pwd, name, role, dept_code, ward_code, officer_level, designation in staff_specs:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                name=name,
                email=email,
                password_hash=hash_password(pwd),
                role=role,
                preferred_lang="en",
                consent_accepted_at=now,
                is_active=True,
            )
            db.add(user)
            db.flush()
        if officer_level and dept_code:
            off = db.query(Officer).filter(Officer.user_id == user.id).first()
            if not off:
                off = Officer(
                    user_id=user.id,
                    dept_id=dept_map[dept_code].id,
                    ward_id=ward_map[ward_code].id if ward_code else None,
                    level=officer_level,
                    designation=designation,
                    is_available=True,
                )
                db.add(off)
                db.flush()
            officer_by_email[email] = off

    # Initial Phase 1 sample grievances (idempotent by ticket_id)
    samples = [
        {
            "ticket_id": "GRV-2026-100001",
            "user_id": citizen.id,
            "is_anonymous": False,
            "title": "No municipal water supply for 3 days in Connaught Place Block B",
            "text": "Tap water supply has completely stopped since Tuesday morning in Block B. Residents are forced to buy water tankers.",
            "language": "en",
            "category": "water",
            "priority": "high",
            "status": "in_progress",
            "ward_code": "W-01",
            "dept_code": "water",
            "officer_email": "officer.water@demo.gov.in",
            "address": "Block B, Connaught Place, New Delhi",
            "lat": 28.6318,
            "lng": 77.2175,
        },
        {
            "ticket_id": "GRV-2026-100002",
            "user_id": citizen.id,
            "is_anonymous": False,
            "title": "Deep pothole near Karol Bagh Metro Pillar 92",
            "text": "A 3-foot wide pothole filled with rainwater is causing two-wheeler accidents every evening near Metro Pillar 92.",
            "language": "en",
            "category": "roads",
            "priority": "high",
            "status": "assigned",
            "ward_code": "W-02",
            "dept_code": "roads",
            "officer_email": "officer.roads@demo.gov.in",
            "address": "Pusa Road, Karol Bagh, New Delhi",
            "lat": 28.6442,
            "lng": 77.1889,
        },
        {
            "ticket_id": "GRV-2026-100003",
            "user_id": None,
            "is_anonymous": True,
            "anon_code": "ANON-DEMO1234",
            "title": "Streetlights not working on Rohini Sector 7 main market road",
            "text": "All 12 LED streetlights between Gate 2 and Gate 4 have been off for a week, making the stretch unsafe at night.",
            "language": "en",
            "category": "electricity",
            "priority": "medium",
            "status": "submitted",
            "ward_code": "W-03",
            "dept_code": "electricity",
            "officer_email": None,
            "address": "Sector 7 Main Market, Rohini, New Delhi",
            "lat": 28.7050,
            "lng": 77.1040,
        },
    ]

    for s in samples:
        if db.query(Grievance.id).filter(Grievance.ticket_id == s["ticket_id"]).first():
            continue
        off = officer_by_email.get(s["officer_email"]) if s["officer_email"] else None
        g = Grievance(
            ticket_id=s["ticket_id"],
            user_id=s["user_id"],
            is_anonymous=s["is_anonymous"],
            anonymous_code_hash=hash_token(s["anon_code"]) if s.get("anon_code") else None,
            title=s["title"],
            text=s["text"],
            language=s["language"],
            category=s["category"],
            priority=s["priority"],
            status=s["status"],
            ward_id=ward_map[s["ward_code"]].id,
            dept_id=dept_map[s["dept_code"]].id,
            assigned_officer_id=off.id if off else None,
            address=s["address"],
            lat=s["lat"],
            lng=s["lng"],
            sla_deadline=now + timedelta(hours=24),
            estimated_resolution_at=now + timedelta(hours=24),
        )
        db.add(g)
        db.flush()
        db.add(
            StatusHistory(
                grievance_id=g.id,
                from_status=None,
                to_status="submitted",
                changed_by_user_id=s["user_id"],
                remarks="Grievance registered",
                is_system_action=False,
            )
        )
        if s["status"] in ("assigned", "in_progress"):
            db.add(
                StatusHistory(
                    grievance_id=g.id,
                    from_status="submitted",
                    to_status="assigned",
                    changed_by_user_id=None,
                    remarks="Assigned to ward officer",
                    is_system_action=True,
                )
            )
        if s["status"] == "in_progress":
            db.add(
                StatusHistory(
                    grievance_id=g.id,
                    from_status="assigned",
                    to_status="in_progress",
                    changed_by_user_id=off.user_id if off else None,
                    remarks="Field inspection scheduled",
                    is_system_action=False,
                )
            )

    db.commit()
