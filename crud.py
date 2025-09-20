from sqlalchemy.orm import Session
import models, schemas

# ----- Sections -----
def get_sections(db: Session):
    return db.query(models.Section).all()

def create_section(db: Session, section: schemas.SectionCreate):
    db_section = models.Section(section_name=section.section_name)
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


# ----- Subjects -----
def get_subjects_by_section(db: Session, section_id: int):
    return (
        db.query(models.Subject)
        .join(models.Course, models.Subject.course_id == models.Course.id)
        .join(models.Section, models.Section.course_id == models.Course.id)
        .filter(models.Section.id == section_id)
        .all()
    )


def create_subject(db: Session, subject: schemas.SubjectCreate):
    db_subject = models.Subject(
        subject_name=subject.subject_name,
        teacher_name=subject.teacher_name,   # ✅ store teacher
        section_id=subject.section_id
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject
