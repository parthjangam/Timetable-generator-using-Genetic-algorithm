from django.http import request
from django.shortcuts import render, redirect
from . forms import *
from .models import *
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .render import Render
from django.views.generic import View
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from .genetic_algorithm import generate_timetable, TimetableData


############################################################################


def index(request):
    return render(request, 'index.html', {})


def about(request):
    return render(request, 'aboutus.html', {})


def help(request):
    return render(request, 'help.html', {})


def terms(request):
    return render(request, 'terms.html', {})




#################################################################################

@login_required
def admindash(request):
    return render(request, 'admindashboard.html', {})

#################################################################################

@login_required 
def addCourses(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        print("Form data:", request.POST)  # Debug print
        
        if form.is_valid():
            print("Form is valid")  # Debug print
            try:
                course = form.cleaned_data
                year = course['year']
                department = Department.objects.get(id=course['department'].id)  # Get the selected department
                
                # Validate year exists in department
                year_exists = False
                year_name = getattr(department, f'year{year}_name', None)
                if year_name:
                    year_exists = True
                
                if not year_exists:
                    raise ValidationError(f'Year {year} does not exist in department {department.dept_name}')
                
                # Save the form and add success message
                course = form.save()
                messages.success(request, f'Course {course.course_number} - {course.course_name} created successfully!')
                return redirect('editcourse')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                print(f"Exception in form processing: {str(e)}")  # Debug print
                messages.error(request, f'Error saving course: {str(e)}')
        else:
            print("Form errors:", form.errors)  # Debug print
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CourseForm()
    
    context = {
        'form': form,
        'departments': Department.objects.all()
    }
    return render(request, 'addCourses.html', context)

@login_required
def course_list_view(request):
    context = {
        'courses': Course.objects.all()
    }
    return render(request, 'courseslist.html', context)

@login_required
def delete_course(request, pk):
    crs = Course.objects.filter(pk=pk)
    if request.method == 'POST':
        crs.delete()
        return redirect('editcourse')

#################################################################################

@login_required
def addInstructor(request): 
    form = InstructorForm(request.POST or None) 
    if request.method == 'POST': 
        if form.is_valid():
            uid = form.cleaned_data.get('uid')
            if Instructor.objects.filter(uid=uid).exists():
                messages.error(request, 'Instructor ID already exists!')
                return redirect('addInstructors')
            form.save() 
            messages.success(request, 'Instructor added successfully!')
            return redirect('addInstructors') 
    context = { 
        'form': form 
    } 
    return render(request, 'addInstructors.html', context)

@login_required
def inst_list_view(request):
    context = {
        'instructors': Instructor.objects.all()
    }
    return render(request, 'inslist.html', context)

@login_required
def delete_instructor(request, pk):
    inst = Instructor.objects.filter(pk=pk)
    if request.method == 'POST':
        inst.delete()
        return redirect('editinstructor')

#################################################################################

@login_required
def addRooms(request):
    form = RoomForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addRooms')
    context = {
        'form': form
    }
    return render(request, 'addRooms.html', context)

@login_required
def room_list(request):
    context = {
        'rooms': Room.objects.all()
    }
    return render(request, 'roomslist.html', context)

@login_required
def delete_room(request, pk):
    rm = Room.objects.filter(pk=pk)
    if request.method == 'POST':
        rm.delete()
        return redirect('editrooms')

#################################################################################

@login_required
def addTimings(request):
    if request.method == 'POST':
        num_days = int(request.POST.get('num_days', 0))
        success = True
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        try:
            # First, clear existing time slots to avoid duplicates
            TimeSlot.objects.all().delete()

            # Create new time slots for each day
            for i in range(num_days):
                day = days[i]
                total_slots = int(request.POST.get(f'day{i}_total_slots', 0))
                
                if total_slots > 0:
                    TimeSlot.objects.create(
                        day=day,
                        total_slots=total_slots
                    )

            messages.success(request, 'Time slots saved successfully!')
            return redirect('editmeetingtime')
        except Exception as e:
            success = False
            messages.error(request, f'Error saving time slots: {str(e)}')

    return render(request, 'addTimings.html')

@login_required
def meeting_list_view(request):
    time_slots = TimeSlot.objects.all().order_by('day')
    context = {
        'time_slots': time_slots
    }
    return render(request, 'mtlist.html', context)

@login_required
def delete_meeting_time(request, pk):
    try:
        time_slot = TimeSlot.objects.get(pk=pk)
        time_slot.delete()
        messages.success(request, 'Time slot deleted successfully!')
    except TimeSlot.DoesNotExist:
        messages.error(request, 'Time slot not found!')
    return redirect('editmeetingtime')
#################################################################################

@login_required
def addDepts(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            department = form.save()
            
            # Save divisions for each year
            for year in range(1, department.num_years + 1):
                num_divisions = getattr(department, f'year{year}_divisions')
                for div_num in range(1, num_divisions + 1):
                    division_name = request.POST.get(f'year{year}_division{div_num}')
                    if division_name:
                        Division.objects.create(
                            department=department,
                            year_number=year,
                            division_number=div_num,
                            division_name=division_name
                        )
            
            return redirect('addDepts')
    context = {
        'form': form
    }
    return render(request, 'addDepts.html', context)

@login_required
def department_list(request):
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'deptlist.html', context)

@login_required
def delete_department(request, pk):
    dept = Department.objects.filter(pk=pk)
    if request.method == 'POST':
        dept.delete()
        return redirect('editdepartment')

#################################################################################

@login_required
def addSections(request):
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('editsection')  # Changed from 'seclist' to 'editsection'
    departments = Department.objects.all()
    courses = Course.objects.all()
    teachers = Instructor.objects.all()
    
    if request.method == 'POST':
        form = SectionForm(request.POST)
        print("Form data:", request.POST)  # Debug print
        
        if form.is_valid():
            print("Form is valid")  # Debug print
            try:
                dept = form.cleaned_data['department']
                year = form.cleaned_data['year']
                division = form.cleaned_data['division']
                course = form.cleaned_data['course']
                teachers = form.cleaned_data['teacher']
                
                print(f"Cleaned data: dept={dept}, year={year}, division={division}")  # Debug print
                
                # Validate year exists in department
                year_exists = False
                for i in range(1, 7):
                    year_name = getattr(dept, f'year{i}_name', None)
                    if year_name == year or str(i) == str(year):
                        year_exists = True
                        break
                
                if not year_exists:
                    raise ValidationError(f'Year {year} does not exist in department {dept.dept_name}')
                
                # Generate section_id if not provided
                if not form.cleaned_data.get('section_id'):
                    section_id = f"{dept.dept_code}_{year}_{division.division_name}_{course.course_number}"
                    form.instance.section_id = section_id
                
                # Save the form and add success message
                section = form.save()
                year_name = section.get_year_name()
                messages.success(request, f'Section {section.section_id} created successfully with year {year_name}!')
                return redirect('editsection')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                print(f"Exception in form processing: {str(e)}")  # Debug print
                messages.error(request, f'Error saving section: {str(e)}')
        else:
            print("Form errors:", form.errors)  # Debug print
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SectionForm()
    
    # Get available years for each department
    dept_years = {}
    for dept in departments:
        years = []
        for i in range(1, 7):
            year_name = getattr(dept, f'year{i}_name', None)
            if year_name:
                years.append({
                    'number': i,
                    'name': year_name
                })
        dept_years[dept.id] = years
    
    context = {
        'form': form,
        'departments': departments,
        'courses': courses,
        'teachers': teachers,
        'dept_years': dept_years,
    }
    return render(request, 'addSections.html', context)

@login_required
def section_list(request):
    # Get all departments with their details
    departments = Department.objects.all()
    
    # Get all sections with related data
    sections = Section.objects.select_related('department', 'course', 'teacher', 'division').all()
    
    context = {
        'departments': departments,
        'sections': sections
    }
    return render(request, 'seclist.html', context)

@login_required
def delete_section(request, pk):
    section = Section.objects.filter(pk=pk)
    if request.method == 'POST':
        section.delete()
        return redirect('editsection')

@login_required
def get_department_years(request):
    """AJAX view to get years for a department"""
    department_id = request.GET.get('department_id')
    if not department_id:
        return JsonResponse({'error': 'No department ID provided'}, status=400)
    
    try:
        department = Department.objects.get(id=department_id)
        years = []
        for i in range(1, 7):
            year_name = getattr(department, f'year{i}_name', None)
            if year_name:
                years.append({
                    'number': i,
                    'name': year_name
                })
        return JsonResponse({'years': years})
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)

@login_required
def get_divisions(request):
    """AJAX view to get divisions for a department and year"""
    department_id = request.GET.get('department_id')
    year = request.GET.get('year')
    
    if not department_id or not year:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        divisions = Division.objects.filter(
            department_id=department_id,
            year_number=year
        ).values('id', 'division_name')
        
        return JsonResponse({'divisions': list(divisions)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#################################################################################

@login_required
def generate(request):
    """Display the generate timetable form"""
    if request.method == 'POST':
        # If form is submitted, redirect to timetable view
        return redirect('timetable')
    
    return render(request, 'generate.html', {
        'departments': Department.objects.all(),
        'time_slots': TimeSlot.objects.all()
    })

@login_required
def timetable(request):
    """Generate and display the timetable"""
    if request.method == 'POST':
        try:
            # Use the imported generate_timetable function from genetic_algorithm.py
            result = generate_timetable()
            
            # Store the timetable in session for PDF generation
            request.session['timetable_data'] = result
            
            # Get all stored timetable entries and organize them
            stored_entries = GeneratedTimetable.objects.select_related(
                'department', 'division', 'course', 'teacher', 'room'
            ).order_by('department', 'year', 'division', 'day', 'time_slot')
            
            # Format the data for template
            formatted_timetable = {}
            
            for entry in stored_entries:
                dept_id = entry.department.id
                year = entry.year
                div_id = entry.division.id
                
                # Initialize department if not exists
                if dept_id not in formatted_timetable:
                    formatted_timetable[dept_id] = {
                        'name': entry.department.dept_name,
                        'years': {}
                    }
                
                # Initialize year if not exists
                if year not in formatted_timetable[dept_id]['years']:
                    formatted_timetable[dept_id]['years'][year] = {
                        'divisions': {}
                    }
                
                # Initialize division if not exists
                if div_id not in formatted_timetable[dept_id]['years'][year]['divisions']:
                    formatted_timetable[dept_id]['years'][year]['divisions'][div_id] = {
                        'name': entry.division.division_name,
                        'days': {}
                    }
                
                # Initialize day if not exists
                if entry.day not in formatted_timetable[dept_id]['years'][year]['divisions'][div_id]['days']:
                    formatted_timetable[dept_id]['years'][year]['divisions'][div_id]['days'][entry.day] = {}
                
                # Add class data to the appropriate slot - convert time_slot to string to match template
                slot_num = str(entry.time_slot)
                formatted_timetable[dept_id]['years'][year]['divisions'][div_id]['days'][entry.day][slot_num] = {
                    'course': entry.course.course_name,
                    'teacher': entry.teacher.name,
                    'room': entry.room.r_number,
                    'course_type': entry.course.course_type
                }
            
            return render(request, 'gentimetable.html', {
                'timetable': formatted_timetable,
                'fitness': result['fitness'],
                'conflicts': result['conflicts'],
                'generations': result['generations'],
                'time_slots': TimeSlot.objects.all()
            })
            
        except Exception as e:
            messages.error(request, f'Error generating timetable: {str(e)}')
            return redirect('admindash')
    else:
        # If someone tries to access this page directly without POST
        return redirect('admindash')

class Pdf(View):
    def get(self, request):
        # Get timetable data from session
        timetable_data = request.session.get('timetable_data', None)
        
        if not timetable_data:
            messages.error(request, "No timetable data found. Please generate a timetable first.")
            return redirect('generate')
        
        params = {
            'request': request,
            'timetable': timetable_data['timetable'],
            'fitness': timetable_data['fitness'],
            'conflicts': timetable_data['conflicts'],
            'generations': timetable_data['generations'],
            'departments': Department.objects.all(),
            'time_slots': TimeSlot.objects.all()
        }
        
        return Render.render('gentimetable.html', params)

@login_required
def get_divisions(request):
    department_id = request.GET.get('department_id')
    year_number = request.GET.get('year_number')
    divisions = []
    if department_id and year_number:
        divisions_qs = Division.objects.filter(department_id=department_id, year_number=year_number)
        for div in divisions_qs:
            divisions.append({'id': div.id, 'name': div.division_name})
    return JsonResponse({'divisions': divisions})



#################################################################################

@login_required
def generate(request):
    """Display the generate timetable form"""
    if request.method == 'POST':
        # If form is submitted, redirect to timetable view
        return redirect('timetable')
    
    return render(request, 'generate.html', {
        'departments': Department.objects.all(),
        'time_slots': TimeSlot.objects.all()
    })


class Pdf(View):
    def get(self, request):
        # Get timetable data from session
        timetable_data = request.session.get('timetable_data', None)
        
        if not timetable_data:
            messages.error(request, "No timetable data found. Please generate a timetable first.")
            return redirect('generate')
        
        params = {
            'request': request,
            'timetable': timetable_data['timetable'],
            'fitness': timetable_data['fitness'],
            'conflicts': timetable_data['conflicts'],
            'generations': timetable_data['generations'],
            'departments': Department.objects.all(),
            'time_slots': TimeSlot.objects.all()
        }
        
        return Render.render('gentimetable.html', params)

@login_required
def get_department_years(request):
    department_id = request.GET.get('department_id')
    print(f"\nDEBUG - get_department_years called with ID: {department_id}")
    
    if not department_id:
        print("DEBUG - No department ID provided")
        return JsonResponse({'years': []})
        
    try:
        department = Department.objects.get(id=department_id)
        print(f"\nDEBUG - Found department:")
        print(f"Name: {department.dept_name}")
        print(f"Code: {department.dept_code}")
        print(f"Num Years: {department.num_years}")
        print(f"Year1: {department.year1_name}")
        print(f"Year2: {department.year2_name}")
        print(f"Year3: {department.year3_name}")
        print(f"Year4: {department.year4_name}")
        
        years = []
        
        # Only add years that have names configured
        for year_num in range(1, department.num_years + 1):
            year_name = getattr(department, f'year{year_num}_name')
            print(f"DEBUG - Checking year {year_num}: {year_name}")
            if year_name:  # Only add if the year name exists and is not empty
                years.append({
                    'year_number': year_num,
                    'year_name': year_name
                })
        
        print(f"DEBUG - Final years list: {years}")
        return JsonResponse({'years': years})
        
    except Department.DoesNotExist:
        print(f"DEBUG - Department with ID {department_id} not found")
        return JsonResponse({'years': [], 'error': 'Department not found'})
    except Exception as e:
        print(f"DEBUG - Error in get_department_years: {str(e)}")
        return JsonResponse({'years': [], 'error': str(e)})


