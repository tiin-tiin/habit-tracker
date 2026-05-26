import json, calendar
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegisterForm, LoginForm, HabitForm
from .models import Habit, CheckIn

# Auth Views
def home(request):
    if request.user.is_authenticated: return redirect('dashboard')
    return render(request, 'habits/home.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            login(request, form.save())
            return redirect('dashboard')
    else: form = RegisterForm()
    return render(request, 'habits/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            u, p = form.cleaned_data.get('username'), form.cleaned_data.get('password')
            user = authenticate(username=u, password=p)
            if user: login(request, user); return redirect('dashboard')
            else:
                return render(request, 'habits/login.html', {
                    'error': 'Invalid username or password.'
                })
    else: form = LoginForm()
    return render(request, 'habits/login.html', {'form': form})

def logout_view(request):
    logout(request); return redirect('home')

# AJAX Validations
@require_http_methods(["POST"])
def validate_username(request):
    u = request.POST.get('username', '').strip()
    exists = User.objects.filter(username__iexact=u).exists()
    return JsonResponse({'valid': not exists, 'message': 'Username taken' if exists else ''})

@require_http_methods(["POST"])
def validate_email(request):
    e = request.POST.get('email', '').strip()
    exists = User.objects.filter(email__iexact=e).exists()
    return JsonResponse({'valid': not exists, 'message': 'Email registered' if exists else ''})

# Dashboard & Tracking
@login_required
def dashboard(request):
    habits = Habit.objects.filter(user=request.user, is_active=True)
    today = date.today()
    todays_checkins = CheckIn.objects.filter(habit__user=request.user, date=today, is_hidden=False)
    selected_year = int(request.GET.get('year', today.year))
    available_years = [today.year, today.year - 1, today.year - 2]
    max_month = today.month if selected_year == today.year else 12
    months = [{'num': m, 'name': calendar.month_name[m][:3], 'full_name': calendar.month_name[m]} for m in range(1, max_month+1)]
    months.reverse()
    return render(request, 'habits/dashboard.html', {
        'habits': habits, 'total_habits': habits.count(), 'current_year': selected_year, 
        'available_years': available_years, 'months': months, 'todays_checkins': todays_checkins
    })

@login_required
def month_view(request, year, month):
    _, num_days = calendar.monthrange(year, month)
    active_habits = Habit.objects.filter(user=request.user, is_active=True)
    
    
    for d in range(1, num_days + 1):
        curr_date = date(year, month, d)
        for h in active_habits:
            CheckIn.objects.get_or_create(habit=h, date=curr_date)
            
    days_data = []
    
    month_checkins = CheckIn.objects.filter(
        habit__user=request.user, 
        date__year=year, 
        date__month=month,
        is_hidden=False
    )
    
    m_comp = month_checkins.filter(checked=True).count()
    m_pot = month_checkins.count()
    
    for d in range(1, num_days + 1):
        curr = date(year, month, d)
        day_checks = month_checkins.filter(date=curr)
        ass, comp = day_checks.count(), day_checks.filter(checked=True).count()
        days_data.append({'date': curr, 'day_num': d, 'opacity': max(0.1, comp/ass if ass > 0 else 0), 'is_today': curr == date.today()})
    
    growth = (m_comp / m_pot * 100) if m_pot > 0 else 0
    tree = 'tree.gif' if growth > 80 else 'young_tree.gif' if growth > 60 else 'bigger_plant.gif' if growth > 40 else 'plant.gif' if growth > 20 else 'sapling.gif'

    return render(request, 'habits/month_view.html', {
        'month_name': calendar.month_name[month], 'year': year, 'month': month, 
        'days': days_data, 'growth_percent': int(growth), 'tree_stage': tree
    })

@login_required
def daily_checkin(request, year, month, day):
    target = date(year, month, day)
    today = date.today()
    active = Habit.objects.filter(user=request.user, is_active=True)


    if target != today:
        if target < today:
            messages.error(request, "You cannot modify habits for past dates.")
        else:
            messages.error(request, "You cannot log habits for the future!")
        return redirect('month_view', year=year, month=month)


    if request.method == 'POST':
        
        if 'remove_habit' in request.POST:
            hid = request.POST.get('remove_habit')
            checkin = get_object_or_404(CheckIn, habit_id=hid, date=target, habit__user=request.user)
            checkin.is_hidden = True
            checkin.save()
            return redirect('daily_checkin', year=year, month=month, day=day)
            
        
        elif 'restore_habit' in request.POST:
            hid = request.POST.get('restore_habit')
            checkin = get_object_or_404(CheckIn, habit_id=hid, date=target, habit__user=request.user)
            checkin.is_hidden = False
            checkin.save()
            return redirect('daily_checkin', year=year, month=month, day=day)
        
        
        elif request.POST.get('action') == 'save_checkins':
            checked_ids = [int(i) for i in request.POST.getlist('habits')]
            assigned = CheckIn.objects.filter(habit__user=request.user, date=target, is_hidden=False)
            
            for c in assigned:
                c.checked = c.habit.id in checked_ids
                c.save()
                
            return redirect('month_view', year=year, month=month)

    
    for h in active: CheckIn.objects.get_or_create(habit=h, date=target)
    
    
    checkins = CheckIn.objects.filter(habit__user=request.user, date=target, is_hidden=False).select_related('habit')
    
    hidden_checkins = CheckIn.objects.filter(habit__user=request.user, date=target, is_hidden=True).select_related('habit')
    
    grouped = {}
    for c in checkins:
        cat = c.habit.category or 'General'
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(c)
        
    return render(request, 'habits/daily_checkin.html', {
        'target_date': target, 
        'grouped_data': grouped, 
        'hidden_checkins': hidden_checkins, 
        'year': year, 
        'month': month
    })
# Habit Management
@login_required
def manage_habits(request):
    habits = Habit.objects.filter(user=request.user).order_by('category')
    grouped = {}
    for h in habits:
        cat = h.category or 'General'
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(h)
    return render(request, 'habits/manage_habits.html', {'grouped_habits': grouped})

@login_required
def add_habit(request):
    if request.method == 'POST':
        form = HabitForm(request.POST, user=request.user)
        if form.is_valid():
            h = form.save(commit=False); h.user = request.user; h.save()
            return redirect('manage_habits')
    return render(request, 'habits/add_habit.html', {'form': HabitForm(user=request.user), 'title': 'Add New Habit'})

@login_required
def edit_habit(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit, user=request.user)
        if form.is_valid():
            form.save(); return redirect('manage_habits')
    return render(request, 'habits/add_habit.html', {'form': HabitForm(instance=habit, user=request.user), 'title': 'Edit Habit'})

@login_required
def delete_habit(request, habit_id):
    h = get_object_or_404(Habit, id=habit_id, user=request.user)
    if request.method == 'POST': h.delete(); return redirect('manage_habits')
    return render(request, 'habits/delete_habit.html', {'habit': h})

@login_required
@require_http_methods(["POST"])
def api_toggle_checkin(request):
    hid = request.POST.get('habit_id')
    dt = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
    c, _ = CheckIn.objects.get_or_create(habit_id=hid, date=dt)
    c.checked = not c.checked; c.save()
    return JsonResponse({'success': True, 'is_checked': c.checked})