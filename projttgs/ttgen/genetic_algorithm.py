from django.db import models
from .models import Room, TimeSlot, Instructor, Course, Department, Section, Division, GeneratedTimetable
import math
import random as rnd
import copy  # Add this import

# Constants for genetic algorithm
POPULATION_SIZE = 9
NUMB_OF_ELITE_SCHEDULES = 1
TOURNAMENT_SELECTION_SIZE = 3
MUTATION_RATE = 0.1

class TimetableData:
    """Class to hold all the data needed for timetable generation"""
    def __init__(self):
        self._rooms = Room.objects.all()
        self._timeSlots = TimeSlot.objects.all()
        self._instructors = Instructor.objects.all()
        self._courses = Course.objects.all()
        self._departments = Department.objects.all()
        self._sections = Section.objects.all()
        self._divisions = Division.objects.all()

    def get_rooms(self): 
        return self._rooms

    def get_instructors(self): 
        return self._instructors

    def get_courses(self): 
        return self._courses

    def get_departments(self): 
        return self._departments
    
    def get_timeSlots(self): 
        return self._timeSlots
    
    def get_sections(self):
        return self._sections
    
    def get_divisions(self):
        return self._divisions

class Class:
    """Represents a single class in the timetable"""
    def __init__(self, section, room=None, instructor=None, time_slot=None, slot_index=None):
        self.section = section
        self.room = room
        self.instructor = instructor
        self.time_slot = time_slot
        self.slot_index = slot_index  # Index within the day's slots (1-based)
        
    def __str__(self):
        return f"{self.section.course.course_name} - {self.section.teacher.name} - {self.time_slot.day} Slot {self.slot_index} - {self.room.r_number}"

class Schedule:
    """Represents a complete timetable schedule"""
    def __init__(self, data):
        self._data = data
        self._classes = []
        self._num_conflicts = 0
        self._fitness = -1
        self._is_fitness_changed = True
        self._class_num = 0
        
    def get_classes(self):
        self._is_fitness_changed = True
        return self._classes
    
    def get_num_conflicts(self):
        return self._num_conflicts
    
    def get_fitness(self):
        if self._is_fitness_changed:
            self._fitness = self.calculate_fitness()
            self._is_fitness_changed = False
        return self._fitness
    
    def initialize(self):
        """Initialize a random schedule"""
        sections = self._data.get_sections()
        rooms = list(self._data.get_rooms())
        time_slots = list(self._data.get_timeSlots())
        
        # Create classes for each section
        for section in sections:
            # Get weekly slots required for this course
            weekly_slots = section.course.weekly_slots
            
            # For each required slot, create a class
            for _ in range(weekly_slots):
                # Randomly select a room and time slot
                room = rnd.choice(rooms)
                time_slot = rnd.choice(time_slots)
                
                # Randomly select a slot index within the day's total slots
                slot_index = rnd.randint(1, time_slot.total_slots)
                
                # Create a new class
                new_class = Class(
                    section=section,
                    room=room,
                    instructor=section.teacher,  # Teacher is already assigned to section
                    time_slot=time_slot,
                    slot_index=slot_index
                )
                
                self._classes.append(new_class)
                
        return self
    
    def calculate_fitness(self):
        """Calculate fitness score based on constraints"""
        self._num_conflicts = 0
        classes = self.get_classes()
        
        # Dictionary to track faculty assignments
        faculty_assignments = {}
        
        # Dictionary to track room assignments
        room_assignments = {}
        
        # Dictionary to track student group assignments
        group_assignments = {}
        
        # Dictionary to track weekly hours per subject for each group
        group_subject_hours = {}
        
        # Check each class for conflicts
        for cls in classes:
            # Constraint 5: Room types must match subject types
            if (cls.section.course.course_type == 'lab' and cls.room.room_type != 'lab') or \
               (cls.section.course.course_type == 'theory' and cls.room.room_type != 'class room'):
                self._num_conflicts += 1
            
            # Create a unique key for the time slot
            time_key = (cls.time_slot.day, cls.slot_index)
            
            # Constraint 1: Faculty cannot teach more than one subject in the same timeslot
            faculty_key = (cls.instructor.id, time_key)
            if faculty_key in faculty_assignments:
                self._num_conflicts += 1
            else:
                faculty_assignments[faculty_key] = cls
            
            # Constraint 2: Room cannot be assigned to more than one group in the same timeslot
            room_key = (cls.room.id, time_key)
            if room_key in room_assignments:
                self._num_conflicts += 1
            else:
                room_assignments[room_key] = cls
            
            # Constraint 3: Student group cannot have more than one subject in the same timeslot
            group_key = ((cls.section.department.id, cls.section.year, cls.section.division.id), time_key)
            if group_key in group_assignments:
                self._num_conflicts += 1
            else:
                group_assignments[group_key] = cls
            
            # Track weekly hours for constraint 4
            subject_group_key = (cls.section.course.id, cls.section.department.id, cls.section.year, cls.section.division.id)
            if subject_group_key not in group_subject_hours:
                group_subject_hours[subject_group_key] = 1
            else:
                group_subject_hours[subject_group_key] += 1
        
        # Constraint 4: Check if weekly hours per subject for each group are satisfied
        for section in self._data.get_sections():
            subject_group_key = (section.course.id, section.department.id, section.year, section.division.id)
            required_hours = section.course.weekly_slots
            actual_hours = group_subject_hours.get(subject_group_key, 0)
            
            if actual_hours != required_hours:
                self._num_conflicts += abs(actual_hours - required_hours)
        
        # Calculate fitness (higher is better)
        return 1 / (1.0 * self._num_conflicts + 1)

def generate_timetable():
    """Generate a timetable using genetic algorithm"""
    data = TimetableData()
    
    # Create initial population
    population = []
    for i in range(POPULATION_SIZE):
        schedule = Schedule(data).initialize()
        population.append(schedule)
    
    # Sort population by fitness
    population.sort(key=lambda x: x.get_fitness(), reverse=True)
    
    # Genetic algorithm
    generation_num = 0
    max_generations = 100  # Limit to prevent infinite loop
    
    while population[0].get_fitness() < 1.0 and generation_num < max_generations:
        generation_num += 1
        print(f"Generation #{generation_num}, Fitness: {population[0].get_fitness()}")
        
        # Create new generation
        new_population = []
        
        # Keep elite schedules
        for i in range(NUMB_OF_ELITE_SCHEDULES):
            new_population.append(population[i])
        
        # Crossover and mutation
        while len(new_population) < POPULATION_SIZE:
            # Tournament selection
            schedule1 = tournament_selection(population)
            schedule2 = tournament_selection(population)
            
            # Crossover
            child = crossover(schedule1, schedule2, data)
            
            # Mutation
            mutate(child, data)
            
            new_population.append(child)
        
        population = new_population
        population.sort(key=lambda x: x.get_fitness(), reverse=True)
    
    # Format the timetable for display
    best_schedule = population[0]
    timetable = format_timetable(best_schedule)
    
    return {
        'timetable': timetable,
        'fitness': best_schedule.get_fitness(),
        'conflicts': best_schedule.get_num_conflicts(),
        'generations': generation_num
    }

def tournament_selection(population):
    """Select a schedule using tournament selection"""
    tournament = []
    for i in range(TOURNAMENT_SELECTION_SIZE):
        tournament.append(population[rnd.randrange(0, len(population))])
    
    tournament.sort(key=lambda x: x.get_fitness(), reverse=True)
    return tournament[0]

def crossover(schedule1, schedule2, data):
    """Create a new schedule by crossing over two parent schedules"""
    child = Schedule(data)
    classes1 = schedule1.get_classes()
    classes2 = schedule2.get_classes()
    
    for i in range(len(classes1)):
        if rnd.random() > 0.5:
            child.get_classes().append(copy.deepcopy(classes1[i]))
        else:
            child.get_classes().append(copy.deepcopy(classes2[i]))
    
    return child

def mutate(schedule, data):
    """Mutate a schedule by randomly changing some classes"""
    for i in range(len(schedule.get_classes())):
        if rnd.random() < MUTATION_RATE:
            # Randomly select a room
            rooms = list(data.get_rooms())
            room = rnd.choice(rooms)
            schedule.get_classes()[i].room = room
            
            # Randomly select a time slot
            time_slots = list(data.get_timeSlots())
            time_slot = rnd.choice(time_slots)
            schedule.get_classes()[i].time_slot = time_slot
            
            # Randomly select a slot index
            slot_index = rnd.randint(1, time_slot.total_slots)
            schedule.get_classes()[i].slot_index = slot_index
    
    return schedule

def format_timetable(schedule):
    """Format the timetable for display and store in database"""
    # Get all unique departments, years, and divisions
    classes = schedule.get_classes()
    
    # Group classes by department, year, division
    timetable = {}
    
    # First clear any existing timetable entries to avoid duplicates
    GeneratedTimetable.objects.all().delete()
    
    # Keep track of used time slots to avoid duplicates
    used_slots = set()
    
    for cls in classes:
        # Make sure section has department, year, and division attributes
        if not hasattr(cls.section, 'department') or not hasattr(cls.section, 'year') or not hasattr(cls.section, 'division'):
            print(f"Warning: Section {cls.section} missing required attributes")
            continue
            
        dept = cls.section.department
        year = cls.section.year
        division = cls.section.division
        
        # Create a unique key for this time slot
        slot_key = (dept.id, year, division.id, cls.time_slot.day, cls.slot_index)
        
        # Skip if this slot is already used
        if slot_key in used_slots:
            print(f"Warning: Duplicate slot detected for {slot_key}")
            continue
            
        used_slots.add(slot_key)
        
        try:
            # Store in database
            GeneratedTimetable.objects.create(
                department=dept,
                year=int(year),
                division=division,
                day=cls.time_slot.day,
                time_slot=cls.slot_index,
                course=cls.section.course,
                teacher=cls.instructor,
                room=cls.room
            )
        except Exception as e:
            print(f"Error creating timetable entry: {e}")
            continue
        
        # Create keys if they don't exist
        if dept.id not in timetable:
            timetable[dept.id] = {'name': dept.dept_name, 'years': {}}
            
        if year not in timetable[dept.id]['years']:
            timetable[dept.id]['years'][year] = {'divisions': {}}
            
        if division.id not in timetable[dept.id]['years'][year]['divisions']:
            timetable[dept.id]['years'][year]['divisions'][division.id] = {
                'name': division.division_name,
                'days': {}
            }
        
        # Add class to appropriate day and slot
        day = cls.time_slot.day
        slot = cls.slot_index
        
        if day not in timetable[dept.id]['years'][year]['divisions'][division.id]['days']:
            timetable[dept.id]['years'][year]['divisions'][division.id]['days'][day] = {}
            
        timetable[dept.id]['years'][year]['divisions'][division.id]['days'][day][slot] = {
            'course': cls.section.course.course_name,
            'teacher': cls.instructor.name,
            'room': cls.room.r_number,
            'course_type': cls.section.course.course_type
        }
    
    return timetable