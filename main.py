from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import calendar
import random
import copy

app = FastAPI(
    title="AI Exam Scheduler with Genetic Algorithm (Anti-Leakage)",
    description="Backend API for multi-day exam scheduling using genetic algorithm with anti-leakage constraints",
    version="4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================
# Data Models
# =======================
class ExamRequest(BaseModel):
    courses: List[str]
    sections: List[str]
    rooms: List[str]
    start_date: str
    end_date: str
    start_time: str
    end_time: str

class TimetableCell(BaseModel):
    course: str
    sections: List[str]  # Multiple sections can share the same exam slot
    rooms: List[str]     # Multiple rooms for the same exam

class TimetableRow(BaseModel):
    date: str
    day_name: str
    formatted_date: str
    time_slots: Dict[str, List[TimetableCell]]  # List to handle multiple exams in same slot

class TimetableResponse(BaseModel):
    timetable: List[TimetableRow]
    time_headers: List[str]
    total_courses: int
    unassigned_courses: int
    fitness_score: float
    generation: int

# =======================
# Helpers
# =======================
def generate_dates(start_date: str, end_date: str) -> List[Dict[str, str]]:
    """Generate exam dates between start and end, skipping Sundays."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta = timedelta(days=1)

    dates = []
    while start <= end:
        if calendar.day_name[start.weekday()] != "Sunday":
            dates.append({
                "date": start.strftime("%Y-%m-%d"),
                "day_name": calendar.day_name[start.weekday()],
                "formatted_date": start.strftime("%A, %B %d, %Y")
            })
        start += delta
    return dates

def generate_timeslots(start_time: str, end_time: str, duration: int = 90) -> List[str]:
    """Generate 1.5 hr time slots between school hours."""
    fmt = "%H:%M"
    start = datetime.strptime(start_time, fmt)
    end = datetime.strptime(end_time, fmt)

    slots = []
    while start + timedelta(minutes=duration) <= end:
        slot_end = start + timedelta(minutes=duration)
        # Format like "4:00 PM - 5:30 PM"
        start_12h = start.strftime("%I:%M %p").lstrip('0')
        end_12h = slot_end.strftime("%I:%M %p").lstrip('0')
        slots.append(f"{start_12h} - {end_12h}")
        start = slot_end
    return slots

def format_course_name(course: str, max_length: int = 25) -> str:
    """Format course name for display."""
    if len(course) <= max_length:
        return course.upper()
    
    words = course.upper().split()
    if len(words) > 1:
        acronym = ''.join(word[0] for word in words if word[0].isalpha())
        if len(acronym) <= max_length:
            return acronym
    
    return course.upper()[:max_length-3] + "..."

# =======================
# Genetic Algorithm Classes
# =======================
class CourseExam:
    """Represents a course exam that all sections must take at the same time."""
    def __init__(self, course: str, sections: List[str]):
        self.course = course
        self.sections = sections  # All sections taking this course
        self.date = None
        self.timeslot = None
        self.rooms = []  # Multiple rooms may be needed for all sections
    
    def __repr__(self):
        return f"CourseExam({self.course}, {len(self.sections)} sections)"

class Schedule:
    def __init__(self, course_exams: List[CourseExam], dates: List[str], rooms: List[str], timeslots: List[str]):
        self.course_exams = course_exams
        self.dates = dates
        self.rooms = rooms
        self.timeslots = timeslots
        self.fitness = 0.0
    
    def randomize(self):
        """Randomly assign date, timeslot, and rooms to each course exam."""
        for course_exam in self.course_exams:
            course_exam.date = random.choice(self.dates)
            course_exam.timeslot = random.choice(self.timeslots)
            
            # Assign rooms for all sections (may need multiple rooms)
            num_sections = len(course_exam.sections)
            num_rooms_needed = min(num_sections, len(self.rooms))
            course_exam.rooms = random.sample(self.rooms, num_rooms_needed)
    
    def calculate_fitness(self) -> float:
        """Calculate fitness score (higher is better)."""
        conflicts = 0
        room_usage = {}  # Track room usage per time slot
        
        # Check for room conflicts (same date, timeslot, room used by different courses)
        for course_exam in self.course_exams:
            if course_exam.date and course_exam.timeslot:
                for room in course_exam.rooms:
                    slot_key = (course_exam.date, course_exam.timeslot, room)
                    if slot_key in room_usage:
                        conflicts += 1
                    else:
                        room_usage[slot_key] = course_exam
        
        # Check for insufficient rooms (if sections > available rooms for a course)
        room_shortage_penalty = 0
        for course_exam in self.course_exams:
            sections_count = len(course_exam.sections)
            rooms_assigned = len(course_exam.rooms)
            if rooms_assigned < sections_count:
                # Penalty for not having enough rooms for all sections
                room_shortage_penalty += (sections_count - rooms_assigned) * 50
        
        # Penalty for conflicts (major issue)
        conflict_penalty = conflicts * 100
        
        # Bonus for even distribution across dates
        date_distribution = {}
        for course_exam in self.course_exams:
            if course_exam.date:
                date_distribution[course_exam.date] = date_distribution.get(course_exam.date, 0) + 1
        
        # Calculate standard deviation of date distribution
        if len(self.dates) > 0:
            mean_exams_per_date = len(self.course_exams) / len(self.dates)
            variance = sum((count - mean_exams_per_date) ** 2 for count in date_distribution.values()) / len(self.dates)
            distribution_penalty = variance * 2
        else:
            distribution_penalty = 0
        
        # Bonus for using multiple rooms efficiently
        room_efficiency_bonus = 0
        for course_exam in self.course_exams:
            if len(course_exam.sections) <= len(course_exam.rooms):
                room_efficiency_bonus += 10
        
        # Higher fitness = better schedule
        self.fitness = (1000 + room_efficiency_bonus) - conflict_penalty - distribution_penalty - room_shortage_penalty
        return self.fitness
    
    def to_timetable_format(self, date_objects: List[Dict[str, str]], timeslots: List[str]) -> Dict[str, Any]:
        """Convert to timetable format for frontend."""
        timetable = []
        
        for date_obj in date_objects:
            date = date_obj["date"]
            
            # Create time slots dict for this date
            time_slots = {}
            for timeslot in timeslots:
                time_slots[timeslot] = []
            
            # Fill in course exams for this date
            for course_exam in self.course_exams:
                if course_exam.date == date and course_exam.timeslot in time_slots:
                    time_slots[course_exam.timeslot].append(TimetableCell(
                        course=format_course_name(course_exam.course),
                        sections=course_exam.sections,
                        rooms=course_exam.rooms
                    ))
            
            timetable.append(TimetableRow(
                date=date,
                day_name=date_obj["day_name"],
                formatted_date=date_obj["formatted_date"],
                time_slots=time_slots
            ))
        
        # Count unassigned courses
        unassigned = len([ce for ce in self.course_exams if not ce.date or not ce.timeslot])
        
        return {
            "timetable": timetable,
            "time_headers": timeslots,
            "total_courses": len(self.course_exams),
            "unassigned_courses": unassigned,
            "fitness_score": self.fitness
        }

class GeneticScheduler:
    def __init__(self, population_size: int = 50, mutation_rate: float = 0.15, generations: int = 200):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.population: List[Schedule] = []
        self.best_schedule: Schedule = None
        self.best_generation = 0
    
    def create_initial_population(self, course_exams: List[CourseExam], dates: List[str], rooms: List[str], timeslots: List[str]):
        """Create initial random population."""
        self.population = []
        for _ in range(self.population_size):
            schedule = Schedule(copy.deepcopy(course_exams), dates, rooms, timeslots)
            schedule.randomize()
            schedule.calculate_fitness()
            self.population.append(schedule)
    
    def selection(self) -> Tuple[Schedule, Schedule]:
        """Tournament selection - pick 2 parents."""
        def tournament():
            tournament_size = 3
            candidates = random.sample(self.population, tournament_size)
            return max(candidates, key=lambda s: s.fitness)
        
        parent1 = tournament()
        parent2 = tournament()
        return parent1, parent2
    
    def crossover(self, parent1: Schedule, parent2: Schedule) -> Tuple[Schedule, Schedule]:
        """Order crossover - combine two schedules."""
        child1_exams = copy.deepcopy(parent1.course_exams)
        child2_exams = copy.deepcopy(parent2.course_exams)
        
        # Crossover point
        crossover_point = random.randint(1, len(child1_exams) - 1)
        
        # Swap assignments after crossover point
        for i in range(crossover_point, len(child1_exams)):
            child1_exams[i].date = parent2.course_exams[i].date
            child1_exams[i].timeslot = parent2.course_exams[i].timeslot
            child1_exams[i].rooms = parent2.course_exams[i].rooms.copy()
            
            child2_exams[i].date = parent1.course_exams[i].date
            child2_exams[i].timeslot = parent1.course_exams[i].timeslot
            child2_exams[i].rooms = parent1.course_exams[i].rooms.copy()
        
        child1 = Schedule(child1_exams, parent1.dates, parent1.rooms, parent1.timeslots)
        child2 = Schedule(child2_exams, parent1.dates, parent1.rooms, parent1.timeslots)
        
        return child1, child2
    
    def mutate(self, schedule: Schedule):
        """Randomly change some assignments."""
        for course_exam in schedule.course_exams:
            if random.random() < self.mutation_rate:
                mutation_type = random.random()
                if mutation_type < 0.4:
                    # Change date
                    course_exam.date = random.choice(schedule.dates)
                elif mutation_type < 0.8:
                    # Change timeslot
                    course_exam.timeslot = random.choice(schedule.timeslots)
                else:
                    # Change room assignment
                    num_sections = len(course_exam.sections)
                    num_rooms_needed = min(num_sections, len(schedule.rooms))
                    course_exam.rooms = random.sample(schedule.rooms, num_rooms_needed)
    
    def evolve(self, course_exams: List[CourseExam], dates: List[str], rooms: List[str], timeslots: List[str]) -> Schedule:
        """Main evolution loop."""
        # Create initial population
        self.create_initial_population(course_exams, dates, rooms, timeslots)
        
        for generation in range(self.generations):
            # Track best schedule
            current_best = max(self.population, key=lambda s: s.fitness)
            if self.best_schedule is None or current_best.fitness > self.best_schedule.fitness:
                self.best_schedule = copy.deepcopy(current_best)
                self.best_generation = generation
            
            # Early stopping if good solution found
            if current_best.fitness >= 1000:
                print(f"Perfect solution found at generation {generation}!")
                break
            
            # Create new generation
            new_population = []
            
            # Keep best individuals (elitism)
            sorted_population = sorted(self.population, key=lambda s: s.fitness, reverse=True)
            elite_count = max(1, self.population_size // 10)
            new_population.extend(sorted_population[:elite_count])
            
            # Create offspring
            while len(new_population) < self.population_size:
                parent1, parent2 = self.selection()
                child1, child2 = self.crossover(parent1, parent2)
                
                self.mutate(child1)
                self.mutate(child2)
                
                child1.calculate_fitness()
                child2.calculate_fitness()
                
                new_population.extend([child1, child2])
            
            # Keep only population_size individuals
            self.population = new_population[:self.population_size]
            
            # Print progress
            if generation % 25 == 0:
                print(f"Generation {generation}: Best fitness = {current_best.fitness:.2f}")
        
        return self.best_schedule

# =======================
# Routes
# =======================
@app.get("/")
def root():
    return {"message": "AI Exam Scheduler with Anti-Leakage Genetic Algorithm v4 is running 🧬🔒"}

@app.post("/schedule", response_model=TimetableResponse)
def generate_schedule(data: ExamRequest):
    """Generate optimized schedule using genetic algorithm with anti-leakage constraints."""
    courses = data.courses
    sections = data.sections
    rooms = data.rooms
    date_objects = generate_dates(data.start_date, data.end_date)
    dates = [d["date"] for d in date_objects]
    timeslots = generate_timeslots(data.start_time, data.end_time)
    
    # Create course exams - each course has all sections taking it at the same time
    course_exams = []
    for course in courses:
        course_exams.append(CourseExam(course, sections.copy()))
    
    print(f"Scheduling {len(course_exams)} courses for {len(sections)} sections using anti-leakage genetic algorithm...")
    print(f"Available slots: {len(dates)} dates × {len(timeslots)} timeslots = {len(dates) * len(timeslots)} total time slots")
    print(f"Available rooms: {len(rooms)} rooms per time slot")
    print(f"CONSTRAINT: All sections must take the same course at the same date and time (anti-leakage)")
    
    # Run genetic algorithm
    scheduler = GeneticScheduler(
        population_size=50,
        mutation_rate=0.15,
        generations=200
    )
    
    best_schedule = scheduler.evolve(course_exams, dates, rooms, timeslots)
    
    print(f"Best solution found at generation {scheduler.best_generation}")
    print(f"Final fitness score: {best_schedule.fitness:.2f}")
    
    # Convert to timetable format
    result = best_schedule.to_timetable_format(date_objects, timeslots)
    result["fitness_score"] = best_schedule.fitness
    result["generation"] = scheduler.best_generation
    
    return TimetableResponse(**result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)