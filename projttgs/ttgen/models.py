from django.db import models
import math
import random as rnd
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, post_delete
from datetime import timedelta, date



POPULATION_SIZE = 9
NUMB_OF_ELITE_SCHEDULES = 1
TOURNAMENT_SELECTION_SIZE = 3
MUTATION_RATE = 0.1

class Department(models.Model):
    dept_name = models.CharField(max_length=50)
    dept_code = models.CharField(max_length=10)
    num_years = models.IntegerField(default=0)
    year1_name = models.CharField(max_length=50, blank=True, null=True)
    year2_name = models.CharField(max_length=50, blank=True, null=True)
    year3_name = models.CharField(max_length=50, blank=True, null=True)
    year4_name = models.CharField(max_length=50, blank=True, null=True)
    year5_name = models.CharField(max_length=50, blank=True, null=True)
    year6_name = models.CharField(max_length=50, blank=True, null=True)
    year1_divisions = models.IntegerField(default=0)
    year2_divisions = models.IntegerField(default=0)
    year3_divisions = models.IntegerField(default=0)
    year4_divisions = models.IntegerField(default=0)
    year5_divisions = models.IntegerField(default=0, blank=True, null=True)
    year6_divisions = models.IntegerField(default=0, blank=True, null=True)
    



    def __str__(self):
        return self.dept_name

class Division(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year_number = models.IntegerField()  # 1 to 6
    division_number = models.IntegerField()  # 1 to max divisions
    division_name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('department', 'year_number', 'division_number')

    def __str__(self):
        return f"{self.department.dept_name} - Year {self.year_number} - Division {self.division_name}"
    

class TimeSlot(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    total_slots = models.IntegerField()

    def __str__(self):
        return f"{self.day} - {self.total_slots} slots"



class Course(models.Model):
    COURSE_TYPES = (
        ('theory', 'Theory'),
        ('lab', 'Lab'),
    )
    id = models.AutoField(primary_key=True)
    course_number = models.CharField(max_length=10, unique=True)
    course_name = models.CharField(max_length=40)
    weekly_slots = models.IntegerField(default=0)
    course_type = models.CharField(max_length=10, choices=COURSE_TYPES, default='theory')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.CharField(
        max_length=50,
        help_text="Year name (e.g. FE, SE, TE, BE)"
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate that the year exists in department
        year_exists = False
        for i in range(1, 7):
            year_name = getattr(self.department, f'year{i}_name', None)
            if str(i) == str(self.year):  # Compare year numbers
                year_exists = True
                break
        if not year_exists:
            raise ValidationError(f'Year {self.year} does not exist in department {self.department.dept_name}')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_year_name(self):
        # Get the actual year name from the department
        year_name = getattr(self.department, f'year{self.year}_name', None)
        return year_name if year_name else self.year

    def __str__(self):
        return f"{self.course_number} - {self.course_name} - {self.weekly_slots} - {self.course_type} - {self.department.dept_name} - {self.get_year_name()}"

class Instructor(models.Model):
    uid = models.CharField(max_length=6)
    name = models.CharField(max_length=25)

    def __str__(self):
        return f'{self.uid} {self.name}'
 
   
class Room(models.Model):
    ROOM_TYPES = (
        ('class room', 'Class Room'),
        ('lab', 'Laboratory'),
    )
    r_number = models.CharField(max_length=6)
    seating_capacity = models.IntegerField(default=0)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='class room')
    

    def __str__(self):
        return f'{self.r_number} {self.room_type} {self.seating_capacity}'



class Section(models.Model):
    section_id = models.AutoField(primary_key=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.CharField(
        max_length=50,
        help_text="Year name (e.g. FE, SE, TE, BE)"
    )
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Instructor, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('department', 'year', 'division', 'course', 'teacher')

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate that the year exists in department
        year_exists = False
        for i in range(1, 7):
            year_name = getattr(self.department, f'year{i}_name', None)
            if str(i) == str(self.year):  # Compare year numbers
                year_exists = True
                break
        if not year_exists:
            raise ValidationError(f'Year {self.year} does not exist in department {self.department.dept_name}')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_year_name(self):
        # Get the actual year name from the department
        year_name = getattr(self.department, f'year{self.year}_name', None)
        return year_name if year_name else self.year

    def __str__(self):
        return f"{self.section_id} - {self.department.dept_name} - {self.get_year_name()} - {self.division.division_name} - {self.course.course_name} - {self.teacher.name}"


class GeneratedTimetable(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField()
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    day = models.CharField(max_length=20)
    time_slot = models.IntegerField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    generation_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['department', 'year', 'division', 'day', 'time_slot']
    