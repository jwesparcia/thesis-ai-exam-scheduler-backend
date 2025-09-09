from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import random

# ----------------------------
# FastAPI Setup
# ----------------------------
app = FastAPI(title="Leakage-Free Exam Scheduler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Request Schema
# ----------------------------
class ScheduleRequest(BaseModel):
    courses: List[str]
    sections: List[str]
    rooms: List[str]
    dates: List[str]
    timeslots: List[str]

# ----------------------------
# Genetic Algorithm Helpers
# ----------------------------

def initialize_population(req: ScheduleRequest, population_size=10):
    """Each individual is a mapping course -> (date, timeslot, [rooms])"""
    population = []
    for _ in range(population_size):
        schedule = {}
        for course in req.courses:
            date = random.choice(req.dates)
            timeslot = random.choice(req.timeslots)

            # Assign rooms (one per section)
            if len(req.sections) > len(req.rooms):
                assigned_rooms = random.sample(req.rooms * (len(req.sections) // len(req.rooms) + 1), len(req.sections))
            else:
                assigned_rooms = random.sample(req.rooms, len(req.sections))

            schedule[course] = {
                "date": date,
                "timeslot": timeslot,
                "rooms": assigned_rooms
            }
        population.append(schedule)
    return population


def fitness(schedule, req: ScheduleRequest):
    """Higher is better: checks room conflicts & anti-leakage rule"""
    score = 100

    for course, details in schedule.items():
        # Anti-leakage: All sections share same date+timeslot
        # Already enforced in initialization

        # Penalize duplicate room assignments
        if len(set(details["rooms"])) < len(details["rooms"]):
            score -= 10

    return score


def select_parents(population, fitnesses):
    return random.choices(population, weights=fitnesses, k=2)


def crossover(parent1, parent2):
    child = {}
    for course in parent1.keys():
        child[course] = random.choice([parent1[course], parent2[course]])
    return child


def mutate(schedule, req: ScheduleRequest, mutation_rate=0.1):
    for course in schedule.keys():
        if random.random() < mutation_rate:
            schedule[course]["date"] = random.choice(req.dates)
            schedule[course]["timeslot"] = random.choice(req.timeslots)

            # reassign rooms uniquely
            schedule[course]["rooms"] = random.sample(req.rooms, len(req.sections))
    return schedule


def run_ga(req: ScheduleRequest, generations=30, pop_size=10):
    population = initialize_population(req, pop_size)
    best_schedule = None
    best_score = -1
    best_gen = 0

    for gen in range(generations):
        fitnesses = [fitness(ind, req) for ind in population]

        for ind, score in zip(population, fitnesses):
            if score > best_score:
                best_schedule = ind
                best_score = score
                best_gen = gen

        new_population = []
        for _ in range(pop_size):
            p1, p2 = select_parents(population, fitnesses)
            child = crossover(p1, p2)
            child = mutate(child, req)
            new_population.append(child)

        population = new_population

    return best_schedule, best_score, best_gen

# ----------------------------
# API Endpoint
# ----------------------------
@app.post("/schedule")
def generate_schedule(req: ScheduleRequest):
    best_schedule, score, generation = run_ga(req)

    # Transform into leakage-free format
    sections_schedule: Dict[str, List[Dict[str, Any]]] = {s: [] for s in req.sections}

    for course, details in best_schedule.items():
        date = details["date"]
        timeslot = details["timeslot"]

        # Each section gets SAME date+timeslot but DIFFERENT room
        for i, section in enumerate(req.sections):
            sections_schedule[section].append({
                "course": course,
                "room": details["rooms"][i % len(details["rooms"])],
                "date": date,
                "timeslot": timeslot
            })

    return {
        "sections": sections_schedule,
        "fitness_score": score,
        "generation": generation,
        "total_courses": len(req.courses),
        "unassigned_courses": 0
    }
