from django.forms import ModelForm
from. models import *
from django import forms

class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = [
            'r_number',
            'seating_capacity',
            'room_type'
        ]
        labels = {
            "r_number": "Room Number",
            "seating_capacity": "Capacity",
            "room_type": "Room Type"
        }
        widgets = {
            'r_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter room number (e.g. A101)'
            }),
            'seating_capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter room capacity'
            }),
            'room_type': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            })
        }


class InstructorForm(ModelForm):
    class Meta:
        model = Instructor
        labels = {
            "uid": "Teacher UID",
            "name": "Full Name"
        }
        fields = [
            'uid',
            'name',
        ]


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['day', 'total_slots']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-control'}),
            'total_slots': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
        }




class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ['course_number', 'department', 'course_name', 'weekly_slots', 'course_type', 'year']
        labels = {
            "course_number": "Course Number",
            "course_name": "Course Name",
            "weekly_slots": "Weekly Slots",
            "course_type": "Course Type",
            "department": "Department",
            "year": "Year"
        }
        widgets = {
            'department': forms.Select(attrs={
                'class': 'form-control',
                'id': 'department',
                'required': True
            }),
            'year': forms.Select(attrs={
                'class': 'form-control',
                'id': 'year',
                'required': True
            })
        }


class DepartmentForm(ModelForm):
    class Meta:
        model = Department
        fields = ['dept_name', 'dept_code', 'num_years', 
                 'year1_name', 'year2_name', 'year3_name', 'year4_name', 
                 'year5_name', 'year6_name',
                 'year1_divisions', 'year2_divisions', 'year3_divisions', 'year4_divisions',
                 'year5_divisions', 'year6_divisions']
        labels = {
            "dept_name": "Department Name",
            "dept_code": "Department Code",
            "num_years": "Number of Years",
            "year1_name": "Name of Year 1",
            "year2_name": "Name of Year 2",
            "year3_name": "Name of Year 3",
            "year4_name": "Name of Year 4",
            "year5_name": "Name of Year 5",
            "year6_name": "Name of Year 6",
            "year1_divisions": "Number of Divisions in Year 1",
            "year2_divisions": "Number of Divisions in Year 2",
            "year3_divisions": "Number of Divisions in Year 3",
            "year4_divisions": "Number of Divisions in Year 4",
            "year5_divisions": "Number of Divisions in Year 5",
            "year6_divisions": "Number of Divisions in Year 6"
        }


class SectionForm(ModelForm):
    class Meta:
        model = Section
        fields = ['section_id', 'department', 'year', 'division', 'course', 'teacher']
        widgets = {
            'section_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter section ID'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control',
                'id': 'department',
                'required': True
            }),
            'year': forms.Select(attrs={
                'class': 'form-control',
                'id': 'year',
                'required': True
            }),
            'division': forms.Select(attrs={
                'class': 'form-control',
                'id': 'division',
                'required': True
            }),
            'course': forms.Select(attrs={
                'class': 'form-control',
                'id': 'course',
                'required': True
            }),
            'teacher': forms.Select(attrs={
                'class': 'form-control',
                'id': 'teacher',
                'required': True
            })
        }
        labels = {
            'section_id': 'Section ID',
            'department': 'Department',
            'year': 'Year',
            'division': 'Division',
            'course': 'Course',
            'teacher': 'Teacher'
        }
       
