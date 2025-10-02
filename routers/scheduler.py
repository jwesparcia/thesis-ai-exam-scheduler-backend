# routers/scheduler.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
import models
import random

router = APIRouter()  # prefix is added in main.py (/scheduler)

# -------------------------
# Request Model
# -------------------------
class ScheduleRequest(BaseModel):
    course_id: int
    year_level_id: int
    semester: int

# -------------------------
# Genetic Algorithm Helpers
# -------------------------
def create_random_schedule(sections, subjects, timeslots, rooms):
    schedule = []
    for section in sections:
        for subj in subjects:
            timeslot = random.choice(timeslots)
            room = random.choice(rooms)

            schedule.append({
                "section_id": section.id,
                "section_name": section.name,
                "subject_id": subj.id,
                "subject_code": subj.code,
                "teacher_id": subj.teacher_id,
                "teacher_name": subj.teacher.name if subj.teacher else "Unassigned",
                "timeslot_id": timeslot.id,
                "room_id": room.id,
            })
    return schedule


def fitness(schedule):
    penalty = 0
    seen = {}

    for exam in schedule:
        key_teacher = (exam["teacher_id"], exam["timeslot_id"])
        key_section = (exam["section_id"], exam["timeslot_id"])
        key_room = (exam["room_id"], exam["timeslot_id"])

        if key_teacher in seen:
            penalty += 5
        else:
            seen[key_teacher] = True

        if key_section in seen:
            penalty += 5
        else:
            seen[key_section] = True

        if key_room in seen:
            penalty += 3
        else:
            seen[key_room] = True

    return penalty


def crossover(parent1, parent2):
    cut = len(parent1) // 2
    return parent1[:cut] + parent2[cut:]


def mutate(schedule, timeslots, rooms, rate=0.1):
    for exam in schedule:
        if random.random() < rate:
            exam["room_id"] = random.choice(rooms).id
        if random.random() < rate:
            exam["timeslot_id"] = random.choice(timeslots).id
    return schedule

# -------------------------
# Main GA Scheduler
# -------------------------
@router.post("/generate")
def generate_exam_schedule(req: ScheduleRequest, db: Session = Depends(get_db)):
    course_id = req.course_id
    year_level_id = req.year_level_id
    semester = req.semester

    # 1. Get sections & subjects
    sections = db.query(models.Section).filter_by(
        course_id=course_id,
        year_level_id=year_level_id
    ).all()
    subjects = db.query(models.Subject).filter_by(
        course_id=course_id,
        year_level_id=year_level_id,
        semester=semester
    ).all()

    if not sections or not subjects:
        return {"message": "No sections/subjects found"}

    # 2. Load timeslots & rooms
    timeslots = db.query(models.Timeslot).all()
    rooms = db.query(models.Room).all()

    if not timeslots or not rooms:
        return {"message": "No rooms or timeslots found in database"}

    # 3. Delete old exams first
    db.query(models.Exam).filter_by(
        course_id=course_id,
        year_level_id=year_level_id,
        semester=semester
    ).delete()
    db.commit()

    # 4. GA parameters
    population_size = 20
    generations = 50

    # 5. Initialize population
    population = [
        create_random_schedule(sections, subjects, timeslots, rooms)
        for _ in range(population_size)
    ]

    # 6. Evolve
    for _ in range(generations):
        population.sort(key=fitness)
        best = population[0]

        next_gen = [best]  # keep best (elitism)
        while len(next_gen) < population_size:
            p1, p2 = random.sample(population[:10], 2)
            child = crossover(p1, p2)
            child = mutate(child, timeslots, rooms)
            next_gen.append(child)
        population = next_gen

    best_schedule = population[0]

    # 7. Save to DB
    for exam in best_schedule:
        db_exam = models.Exam(
            section_id=exam["section_id"],
            subject_id=exam["subject_id"],
            teacher_id=exam["teacher_id"],
            course_id=course_id,
            year_level_id=year_level_id,
            semester=semester,
            timeslot_id=exam["timeslot_id"],
            room_id=exam["room_id"]
        )
        db.add(db_exam)
    db.commit()

    # 8. Query back saved exams with full details
    saved_exams = db.query(models.Exam).filter_by(
    course_id=course_id,
    year_level_id=year_level_id,
    semester=semester
).join(models.Timeslot).order_by(
    models.Timeslot.date.asc(),
    models.Timeslot.start_time.asc()
).all()


    return {
        "message": "Exam schedule generated with GA",
        "exams": [
            {
                "id": exam.id,
                "section_name": exam.section.name if exam.section else None,
                "subject_code": exam.subject.code if exam.subject else None,
                "subject_name": exam.subject.name if exam.subject else None,
                "teacher_name": exam.teacher.name if exam.teacher else "Unassigned",
                "exam_date": exam.timeslot.date.strftime("%B %d, %Y") if exam.timeslot else None,
                "start_time": exam.timeslot.start_time.strftime("%I:%M %p") if exam.timeslot else None,
                "end_time": exam.timeslot.end_time.strftime("%I:%M %p") if exam.timeslot else None,
                "room": exam.room.name if exam.room else None,
            }
            for exam in saved_exams
        ]
    }
