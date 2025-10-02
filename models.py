# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    sections = relationship("Section", back_populates="course")
    subjects = relationship("Subject", back_populates="course")
    exams = relationship("Exam", back_populates="course")


class YearLevel(Base):
    __tablename__ = "year_levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    sections = relationship("Section", back_populates="year_level")
    subjects = relationship("Subject", back_populates="year_level")
    exams = relationship("Exam", back_populates="year_level")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))
    year_level_id = Column(Integer, ForeignKey("year_levels.id"))

    course = relationship("Course", back_populates="sections")
    year_level = relationship("YearLevel", back_populates="sections")
    exams = relationship("Exam", back_populates="section")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    exams = relationship("Exam", back_populates="teacher")
    subjects = relationship("Subject", back_populates="teacher")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True)
    name = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))
    year_level_id = Column(Integer, ForeignKey("year_levels.id"))
    semester = Column(Integer)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

    course = relationship("Course", back_populates="subjects")
    year_level = relationship("YearLevel", back_populates="subjects")
    teacher = relationship("Teacher", back_populates="subjects")
    exams = relationship("Exam", back_populates="subject")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    exams = relationship("Exam", back_populates="room")


class Timeslot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)

    exams = relationship("Exam", back_populates="timeslot")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    section_id = Column(Integer, ForeignKey("sections.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"))

    course_id = Column(Integer, ForeignKey("courses.id"))
    year_level_id = Column(Integer, ForeignKey("year_levels.id"))
    semester = Column(Integer)

    subject = relationship("Subject", back_populates="exams")
    teacher = relationship("Teacher", back_populates="exams")
    section = relationship("Section", back_populates="exams")
    room = relationship("Room", back_populates="exams")
    timeslot = relationship("Timeslot", back_populates="exams")
    course = relationship("Course", back_populates="exams")
    year_level = relationship("YearLevel", back_populates="exams")
