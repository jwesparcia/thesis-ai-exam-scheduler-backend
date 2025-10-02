# seed.py
import random
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

# Reset database
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

db: Session = SessionLocal()

# -------------------------
# Teachers
# -------------------------
teacher_names = [
    "Sir Gascon", "Sir Richard", "Sir Salem", "Sir Esparcia",
    "Sir Jayve", "Sir Besa", "Sir Van", "Sir Mira",
    "Sir Fabricante", "Sir Tabio", "Sir Norman", "Sir Comadre",
    "Sir Manny Jade", "Sir Jed", "Sir Crisostomo", "Sir Garces"
]

teachers = [models.Teacher(name=name) for name in teacher_names]
db.add_all(teachers)
db.commit()
teacher_ids = [t.id for t in db.query(models.Teacher).all()]

# -------------------------
# Courses
# -------------------------
courses = [
    models.Course(name="BSIT"),
    models.Course(name="BSCS"),
]
db.add_all(courses)
db.commit()
courses = db.query(models.Course).all()

# -------------------------
# Year Levels
# -------------------------
year_levels = [
    models.YearLevel(name="1st Year"),
    models.YearLevel(name="2nd Year"),
    models.YearLevel(name="3rd Year"),
    models.YearLevel(name="4th Year"),
]
db.add_all(year_levels)
db.commit()
year_levels = db.query(models.YearLevel).all()

# -------------------------
# Subject Pools
# -------------------------
bsit_subjects = {
    1: {1: ["Intro to IT", "Programming 1", "Digital Logic", "Discrete Math", "PE 1", "NSTP 1", "GE 1"],
        2: ["Programming 2", "Computer Organization", "Data Structures", "PE 2", "NSTP 2", "GE 2", "GE 3"]},
    2: {1: ["Algorithms", "Database Systems", "Operating Systems", "Networking 1", "PE 3", "GE 4", "GE 5"],
        2: ["Software Engineering 1", "Networking 2", "Web Development", "Human-Computer Interaction", "PE 4", "GE 6", "GE 7"]},
    3: {1: ["Software Engineering 2", "Information Assurance", "Mobile Development", "IT Elective 1", "GE 8", "GE 9", "GE 10"],
        2: ["Systems Integration", "Capstone 1", "IT Elective 2", "IT Elective 3", "GE 11", "GE 12", "GE 13"]},
    4: {1: ["Capstone 2", "IT Project Management", "Professional Ethics", "IT Elective 4", "GE 14", "GE 15", "GE 16"],
        2: ["Internship", "IT Trends", "IT Seminar", "IT Elective 5", "GE 17", "GE 18", "GE 19"]}
}

bscs_subjects = {
    1: {1: ["Intro to CS", "Programming 1", "Calculus 1", "Physics 1", "PE 1", "NSTP 1", "GE 1"],
        2: ["Programming 2", "Calculus 2", "Physics 2", "Discrete Structures", "PE 2", "NSTP 2", "GE 2"]},
    2: {1: ["Algorithms", "Computer Architecture", "Data Structures", "Linear Algebra", "PE 3", "GE 3", "GE 4"],
        2: ["Operating Systems", "Theory of Computation", "Probability & Statistics", "Networking 1", "PE 4", "GE 5", "GE 6"]},
    3: {1: ["Programming Languages", "Artificial Intelligence", "Database Systems", "CS Elective 1", "GE 7", "GE 8", "GE 9"],
        2: ["Software Engineering", "Computer Graphics", "CS Elective 2", "CS Elective 3", "GE 10", "GE 11", "GE 12"]},
    4: {1: ["Capstone 1", "Parallel Computing", "Compiler Design", "CS Elective 4", "GE 13", "GE 14", "GE 15"],
        2: ["Capstone 2", "Internship", "CS Seminar", "CS Elective 5", "GE 16", "GE 17", "GE 18"]}
}

# -------------------------
# Generate Sections & Subjects
# -------------------------
sections = []
subjects = []

def generate_subjects(course, year, semester):
    pool = bsit_subjects if "IT" in course.name else bscs_subjects
    subj_names = pool[year.id][semester]
    subject_objs = []
    for i, subj_name in enumerate(subj_names, start=1):
        subj = models.Subject(
            code=f"{course.name[:2].upper()}{year.id}{semester}{i:02d}",
            name=subj_name,
            course_id=course.id,
            year_level_id=year.id,
            semester=semester,
            teacher_id=random.choice(teacher_ids)
        )
        subject_objs.append(subj)
    return subject_objs

for course in courses:
    for year in year_levels:
        for s in range(1, 5):  # 4 sections
            section = models.Section(
                name=f"{course.name}-{year.id}{chr(64+s)}",
                course_id=course.id,
                year_level_id=year.id,
            )
            sections.append(section)

        # Add subjects for both semesters
        for semester in [1, 2]:
            subjects.extend(generate_subjects(course, year, semester))

db.add_all(sections)
db.add_all(subjects)
db.commit()

print("✅ Database seeded successfully!")

# -------------------------
# Rooms
# -------------------------
rooms = [models.Room(name=f"Room {i}") for i in range(101, 111)]  # 10 rooms
db.add_all(rooms)

# -------------------------
# Timeslots (example: 5 days × 2 slots per day)
# -------------------------
# -------------------------
# Timeslots (7:00 AM – 8:30 PM, 1h30 exam + 1h30 break)
# -------------------------
from datetime import date, time, timedelta, datetime

base_date = date.today()
timeslots = []

exam_duration = timedelta(hours=1, minutes=30)
break_duration = timedelta(hours=1, minutes=30)

for d in range(5):  # Generate 5 exam days
    day = base_date + timedelta(days=d)

    current = datetime.combine(day, time(7, 0))   # Start at 7:00 AM
    cutoff = datetime.combine(day, time(20, 30))  # Last slot must end <= 8:30 PM

    while current + exam_duration <= cutoff:
        start_t = current.time()
        end_t = (current + exam_duration).time()

        timeslots.append(models.Timeslot(
            date=day,
            start_time=start_t,
            end_time=end_t
        ))

        # move to next slot (exam + break)
        current += exam_duration + break_duration

db.add_all(timeslots)
db.commit()

print("✅ Database seeded successfully with rooms & 1h30 exam + 1h30 break slots!")

