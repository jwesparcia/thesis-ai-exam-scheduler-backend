#schemas.py
from pydantic import BaseModel

# ----- Section Schemas -----
class SectionBase(BaseModel):
    section_name: str

class SectionCreate(SectionBase):
    pass

class Section(SectionBase):
    id: int
    class Config:
        orm_mode = True


# ----- Subject Schemas -----
class SubjectBase(BaseModel):
    subject_name: str
    teacher_name: str   # ✅ include teacher

class SubjectCreate(SubjectBase):
    section_id: int

class Subject(SubjectBase):
    id: int
    section_id: int
    class Config:
        orm_mode = True
