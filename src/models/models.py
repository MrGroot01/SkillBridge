import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Boolean,
    Enum as SAEnum, Date, Time
)
from sqlalchemy.orm import relationship
from src.core.database import Base
import enum


class UserRole(str, enum.Enum):
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)
    institution_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("User", remote_side=[id], foreign_keys=[institution_id])
    trainer_batches = relationship("BatchTrainer", back_populates="trainer", foreign_keys="BatchTrainer.trainer_id")
    student_batches = relationship("BatchStudent", back_populates="student", foreign_keys="BatchStudent.student_id")
    sessions_created = relationship("Session", back_populates="trainer")
    attendance_records = relationship("Attendance", back_populates="student")


class Batch(Base):
    __tablename__ = "batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    institution_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("User", foreign_keys=[institution_id])
    trainers = relationship("BatchTrainer", back_populates="batch")
    students = relationship("BatchStudent", back_populates="batch")
    invites = relationship("BatchInvite", back_populates="batch")
    sessions = relationship("Session", back_populates="batch")


class BatchTrainer(Base):
    __tablename__ = "batch_trainers"

    batch_id = Column(String(36), ForeignKey("batches.id"), primary_key=True)
    trainer_id = Column(String(36), ForeignKey("users.id"), primary_key=True)

    batch = relationship("Batch", back_populates="trainers")
    trainer = relationship("User", back_populates="trainer_batches", foreign_keys=[trainer_id])


class BatchStudent(Base):
    __tablename__ = "batch_students"

    batch_id = Column(String(36), ForeignKey("batches.id"), primary_key=True)
    student_id = Column(String(36), ForeignKey("users.id"), primary_key=True)

    batch = relationship("Batch", back_populates="students")
    student = relationship("User", back_populates="student_batches", foreign_keys=[student_id])


class BatchInvite(Base):
    __tablename__ = "batch_invites"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("batches.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

    batch = relationship("Batch", back_populates="invites")
    creator = relationship("User", foreign_keys=[created_by])


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("batches.id"), nullable=False)
    trainer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("Batch", back_populates="sessions")
    trainer = relationship("User", back_populates="sessions_created")
    attendance = relationship("Attendance", back_populates="session")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.present)
    marked_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="attendance")
    student = relationship("User", back_populates="attendance_records")
