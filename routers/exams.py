# routers/exams.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter()

# -------------------------
# Get all exams by course/year/semester
# -------------------------
@router.get("/")
def generate_exam_schedule(course_id: int, year_level_id: int, semester: int, db: Session = Depends(get_db)):
    exams = db.query(models.Exam).filter_by(
        course_id=course_id,
        year_level_id=year_level_id,
        semester=semester
    ).all()

    return {"exams": [
        {
            "id": exam.id,
            "subject": exam.subject.name if exam.subject else None,
            "teacher": exam.teacher.name if exam.teacher else None,
            "room": exam.room.name if exam.room else None,
            "section": exam.section.name if exam.section else None,
            "date": exam.timeslot.date.isoformat() if exam.timeslot else None,
            "start_time": str(exam.timeslot.start_time) if exam.timeslot else None,
            "end_time": str(exam.timeslot.end_time) if exam.timeslot else None,
        }
        for exam in exams
    ]}


# -------------------------
# Get a single exam by ID
# -------------------------
@router.get("/{exam_id}")
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(models.Exam).filter_by(id=exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    return {
        "id": exam.id,
        "section": exam.section.name if exam.section else None,
        "subject": {
            "id": exam.subject.id,
            "code": exam.subject.code,
            "name": exam.subject.name
        } if exam.subject else None,
        "teacher": exam.teacher.name if exam.teacher else None,
        "room": exam.room.name if exam.room else None,
        "date": str(exam.timeslot.date) if exam.timeslot else None,
        "start_time": str(exam.timeslot.start_time) if exam.timeslot else None,
        "end_time": str(exam.timeslot.end_time) if exam.timeslot else None,
    }


# -------------------------
# Delete exams for a course/year/semester (useful for reset)
# -------------------------
@router.delete("/")
def delete_exams(course_id: int, year_level_id: int, semester: int, db: Session = Depends(get_db)):
    deleted = db.query(models.Exam).filter_by(
        course_id=course_id,
        year_level_id=year_level_id,
        semester=semester
    ).delete()
    db.commit()

    return {"message": f"{deleted} exam(s) deleted"}
