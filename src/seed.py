"""
Seed script: inserts 2 institutions, 4 trainers, 15 students,
3 batches, 8 sessions, and attendance records.

Run from backend/:
    python -m src.seed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, time, datetime, timedelta
import uuid
from src.core.database import SessionLocal, engine
from src.core.database import Base
from src.models.models import (
    User, Batch, BatchTrainer, BatchStudent, BatchInvite,
    Session, Attendance, UserRole, AttendanceStatus
)
from src.auth.jwt import hash_password

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        print("🌱 Seeding SkillBridge database...")

        # ── Institutions ──────────────────────────────────────────────────────
        inst1 = User(name="Apex Institute", email="apex@skillbridge.in",
                     hashed_password=hash_password("inst1234"),
                     role=UserRole.institution)
        inst2 = User(name="Nova Academy", email="nova@skillbridge.in",
                     hashed_password=hash_password("inst1234"),
                     role=UserRole.institution)
        db.add_all([inst1, inst2])
        db.flush()

        # ── Programme Manager ─────────────────────────────────────────────────
        pm = User(name="Priya Manager", email="pm@skillbridge.in",
                  hashed_password=hash_password("pm1234"),
                  role=UserRole.programme_manager)
        db.add(pm)

        # ── Monitoring Officer ────────────────────────────────────────────────
        mo = User(name="Monitoring Mo", email="monitor@skillbridge.in",
                  hashed_password=hash_password("mo1234"),
                  role=UserRole.monitoring_officer)
        db.add(mo)

        # ── Trainers ──────────────────────────────────────────────────────────
        trainers = []
        trainer_data = [
            ("Arjun Sharma", "arjun@skillbridge.in", inst1.id),
            ("Divya Nair", "divya@skillbridge.in", inst1.id),
            ("Kiran Patel", "kiran@skillbridge.in", inst2.id),
            ("Sneha Rao", "sneha@skillbridge.in", inst2.id),
        ]
        for name, email, inst_id in trainer_data:
            t = User(name=name, email=email,
                     hashed_password=hash_password("trainer1234"),
                     role=UserRole.trainer,
                     institution_id=inst_id)
            db.add(t)
            trainers.append(t)
        db.flush()

        # ── Students ──────────────────────────────────────────────────────────
        students = []
        student_data = [
            ("Aarav Mehta", "aarav@student.in"),
            ("Bhavna Singh", "bhavna@student.in"),
            ("Chirag Joshi", "chirag@student.in"),
            ("Deepika Verma", "deepika@student.in"),
            ("Eshan Kumar", "eshan@student.in"),
            ("Fatima Khan", "fatima@student.in"),
            ("Gaurav Mishra", "gaurav@student.in"),
            ("Hina Ansari", "hina@student.in"),
            ("Ishaan Trivedi", "ishaan@student.in"),
            ("Jaya Pandey", "jaya@student.in"),
            ("Kunal Gupta", "kunal@student.in"),
            ("Lavanya Iyer", "lavanya@student.in"),
            ("Manish Tiwari", "manish@student.in"),
            ("Nisha Reddy", "nisha@student.in"),
            ("Om Prakash", "om@student.in"),
        ]
        for name, email in student_data:
            s = User(name=name, email=email,
                     hashed_password=hash_password("student1234"),
                     role=UserRole.student)
            db.add(s)
            students.append(s)
        db.flush()

        # ── Batches ───────────────────────────────────────────────────────────
        batch1 = Batch(name="Python Fundamentals - Batch A", institution_id=inst1.id)
        batch2 = Batch(name="Data Science Bootcamp", institution_id=inst1.id)
        batch3 = Batch(name="Web Dev with React", institution_id=inst2.id)
        db.add_all([batch1, batch2, batch3])
        db.flush()

        # Assign trainers to batches
        db.add_all([
            BatchTrainer(batch_id=batch1.id, trainer_id=trainers[0].id),
            BatchTrainer(batch_id=batch1.id, trainer_id=trainers[1].id),  # two trainers
            BatchTrainer(batch_id=batch2.id, trainer_id=trainers[1].id),
            BatchTrainer(batch_id=batch3.id, trainer_id=trainers[2].id),
            BatchTrainer(batch_id=batch3.id, trainer_id=trainers[3].id),
        ])

        # Assign students to batches
        for s in students[:6]:
            db.add(BatchStudent(batch_id=batch1.id, student_id=s.id))
        for s in students[5:11]:
            db.add(BatchStudent(batch_id=batch2.id, student_id=s.id))
        for s in students[9:15]:
            db.add(BatchStudent(batch_id=batch3.id, student_id=s.id))
        db.flush()

        # ── Sessions ──────────────────────────────────────────────────────────
        today = date.today()
        sessions_data = [
            # batch1 sessions (trainer[0])
            (batch1.id, trainers[0].id, "Intro to Python",      today - timedelta(days=10), time(9,0),  time(11,0)),
            (batch1.id, trainers[0].id, "Data Types & Control", today - timedelta(days=7),  time(9,0),  time(11,0)),
            (batch1.id, trainers[1].id, "Functions & Modules",  today - timedelta(days=4),  time(9,0),  time(11,0)),
            # batch2 sessions (trainer[1])
            (batch2.id, trainers[1].id, "NumPy Basics",         today - timedelta(days=9),  time(14,0), time(16,0)),
            (batch2.id, trainers[1].id, "Pandas Deep Dive",     today - timedelta(days=6),  time(14,0), time(16,0)),
            # batch3 sessions (trainer[2])
            (batch3.id, trainers[2].id, "HTML & CSS Refresher", today - timedelta(days=8),  time(10,0), time(12,0)),
            (batch3.id, trainers[2].id, "React Components",     today - timedelta(days=5),  time(10,0), time(12,0)),
            (batch3.id, trainers[3].id, "State & Props",        today - timedelta(days=2),  time(10,0), time(12,0)),
        ]
        sessions = []
        for batch_id, trainer_id, title, d, st, et in sessions_data:
            sess = Session(batch_id=batch_id, trainer_id=trainer_id,
                           title=title, date=d, start_time=st, end_time=et)
            db.add(sess)
            sessions.append(sess)
        db.flush()

        # ── Attendance ────────────────────────────────────────────────────────
        statuses = [
            AttendanceStatus.present, AttendanceStatus.present,
            AttendanceStatus.present, AttendanceStatus.late,
            AttendanceStatus.absent,  AttendanceStatus.present,
        ]

        def add_attendance(session_obj, batch_students_list):
            for i, bs in enumerate(batch_students_list):
                db.add(Attendance(
                    session_id=session_obj.id,
                    student_id=bs.id,
                    status=statuses[i % len(statuses)],
                ))

        batch1_students = students[:6]
        batch2_students = students[5:11]
        batch3_students = students[9:15]

        for s in sessions[:3]:
            add_attendance(s, batch1_students)
        for s in sessions[3:5]:
            add_attendance(s, batch2_students)
        for s in sessions[5:8]:
            add_attendance(s, batch3_students)

        db.commit()
        print("✅ Seed complete!")
        print("\n📋 Test accounts (all passwords below):")
        print("  institution : apex@skillbridge.in / inst1234")
        print("  institution : nova@skillbridge.in / inst1234")
        print("  trainer     : arjun@skillbridge.in / trainer1234")
        print("  trainer     : divya@skillbridge.in / trainer1234")
        print("  trainer     : kiran@skillbridge.in / trainer1234")
        print("  trainer     : sneha@skillbridge.in / trainer1234")
        print("  student     : aarav@student.in / student1234")
        print("  prog mgr    : pm@skillbridge.in / pm1234")
        print("  monitoring  : monitor@skillbridge.in / mo1234")
        print("\n  MONITORING_API_KEY: sk-monitoring-hardcoded-key-12345")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
