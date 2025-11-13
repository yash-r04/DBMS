from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from .models import Equipment, Supplier, UsageRecord, Alert, User
from .forms import RegisterForm,EquipmentForm,SupplierForm
from .decorators import admin_required, staff_required, viewer_allowed

from .forms import EquipmentRequestForm
from .models import EquipmentRequest

@login_required
def request_equipment(request):
    if request.method == "POST":
        form = EquipmentRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            messages.success(request, "Request submitted!")
            return redirect('home')
    else:
        form = EquipmentRequestForm()
    return render(request, 'equipment/request_equipment.html', {'form': form})



@login_required
@staff_required
def manage_requests(request):
    pending_requests = EquipmentRequest.objects.filter(status='pending')

    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        req = EquipmentRequest.objects.get(id=req_id)
        
        if action == 'approve':
            eq = req.equipment
            if req.quantity <= eq.quantity:
                eq.quantity -= req.quantity
                eq.save()

                # Update request status
                req.status = 'approved'
                req.processed_at = timezone.now()
                req.save()

                # Automatically create a UsageRecord so it shows as borrowed
                UsageRecord.objects.create(
                    user=req.user,
                    equipment=eq,
                    borrowed_on=timezone.now(),
                    quantity_used=req.quantity,
                    purpose=req.purpose or "Requested via dashboard"
                )

            else:
                messages.error(request, f"Not enough {eq.name} available.")

        elif action == 'reject':
            req.status = 'rejected'
            req.processed_at = timezone.now()
            req.save()
        
        return redirect('manage_requests')

    return render(request, 'equipment/manage_requests.html', {'requests': pending_requests})

# =======================
# Authentication Views
# =======================

def home(request):
    equipments = Equipment.objects.all()[:5]
    return render(request, 'equipment/home.html', {'equipments': equipments})

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after registration
            messages.success(request, f"Welcome {user.username}! You are now logged in.")

            # Redirect based on role
            if user.role == 'Admin':
                return redirect('admin_dashboard')
            elif user.role == 'Staff':
                return redirect('staff_dashboard')
            else:
                return redirect('viewer_dashboard')
        else:
            # Show form errors
            messages.error(request, "Please correct the errors below.")
            print(form.errors)  # For debugging in console
    else:
        form = RegisterForm()

    return render(request, 'equipment/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if user.role == 'Admin':
                return redirect('admin_dashboard')
            elif user.role == 'Staff':
                return redirect('staff_dashboard')
            else:
                return redirect('viewer_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'equipment/login.html')



@login_required
def dashboard(request):
    """Redirect to respective dashboards based on role"""
    role = request.user.role
    if role == 'Admin':
        return redirect('admin_dashboard')
    elif role == 'Staff':
        return redirect('staff_dashboard')
    else:
        return redirect('viewer_dashboard')


# =======================
# Dashboards
# =======================

from django.db.models import Count
from django.utils import timezone

@admin_required
def admin_dashboard(request):
    equipments = Equipment.objects.all()
    suppliers = Supplier.objects.all()
    alerts = Alert.objects.all()
    borrowed_count = UsageRecord.objects.filter(returned_on__isnull=True).count()

    # Analytics: category distribution
    category_data = Equipment.objects.values('category').annotate(count=Count('id'))
    categories = [item['category'] for item in category_data]
    counts = [item['count'] for item in category_data]

    context = {
        'equipments': equipments,
        'supplier_count': suppliers.count(),
        'equipment_count': equipments.count(),
        'borrowed_count': borrowed_count,
        'alert_count': alerts.count(),
        'categories': categories,
        'counts': counts
    }

    return render(request, 'equipment/admin_dashboard.html', context)

@admin_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'equipment/supplier_list.html', {'suppliers': suppliers})

@admin_required
def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added successfully!")
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'equipment/add_supplier.html', {'form': form})

@login_required
@staff_required
def staff_dashboard(request):
    # Stats
    equipment_count = Equipment.objects.count()
    borrowed_records = UsageRecord.objects.filter(returned_on__isnull=True)
    borrowed_count = borrowed_records.count()
    alert_count = Alert.objects.filter(is_active=True).count()

    # Pending requests
    pending_requests = EquipmentRequest.objects.filter(status='pending')

    context = {
        'equipment_count': equipment_count,
        'borrowed_count': borrowed_count,
        'alert_count': alert_count,
        'borrowed_records': borrowed_records,
        'requests': pending_requests,
    }

    # Handle approve/reject POST
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        req = EquipmentRequest.objects.get(id=req_id)

        if action == 'approve':
            eq = req.equipment
            if req.quantity <= eq.quantity:
                eq.quantity -= req.quantity
                eq.save()
                req.status = 'approved'
                req.processed_at = timezone.now()
                req.save()
            else:
                messages.error(request, f"Not enough {eq.name} available.")
        elif action == 'reject':
            req.status = 'rejected'
            req.processed_at = timezone.now()
            req.save()
        
        return redirect('staff_dashboard')

    return render(request, 'equipment/staff_dashboard.html', context)


@login_required
@viewer_allowed
def viewer_dashboard(request):
    equipments = Equipment.objects.all()
    form = EquipmentRequestForm()
    return render(request, 'equipment/viewer_dashboard.html', {
        'equipments': equipments,
        'form': form
    })



def no_permission(request):
    return render(request, 'equipment/no_permission.html')


# =======================
# Equipment Management
# =======================

@login_required
def equipment_list(request):
    equipments = Equipment.objects.all()
    return render(request, 'equipment/equipment_list.html', {'equipments': equipments})


@login_required
def equipment_detail(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    return render(request, 'equipment/equipment_detail.html', {'equipment': equipment})


@admin_required
  
def add_equipment(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('equipment_list')  # or your dashboard
    else:
        form = EquipmentForm()

    return render(request, 'equipment/add_equipment.html', {'form': form})

@admin_required
def equipment_edit(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipment updated successfully!")
            return redirect('equipment_list')
    else:
        form = EquipmentForm(instance=equipment)
    return render(request, 'equipment/equipment_form.html', {'form': form})

@admin_required
def equipment_delete(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, "Equipment deleted successfully!")
        return redirect('equipment_list')
    return render(request, 'equipment/equipment_confirm_delete.html', {'equipment': equipment})

# =======================
# Borrow / Return System
# =======================
@login_required
@viewer_allowed
def request_equipment(request):
    if request.method == "POST":
        form = EquipmentRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            messages.success(request, "Request submitted!")
            return redirect('viewer_dashboard')
    else:
        form = EquipmentRequestForm()
    return render(request, 'equipment/request_equipment.html', {'form': form})

@login_required
def borrow_equipment(request, id):
    equipment = get_object_or_404(Equipment, id=id)

    if equipment.quantity <= 0:
        messages.error(request, "Equipment not available for borrowing.")
        return redirect('equipment_list')

    equipment.quantity -= 1
    equipment.save()

    UsageRecord.objects.create(
        user=request.user,
        equipment=equipment,
        borrowed_on=timezone.now(),
        purpose="General use",
        quantity_used=1
    )

    messages.success(request, f"You have borrowed {equipment.name}.")
    return redirect('equipment_list')


@login_required
def return_equipment(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    record = UsageRecord.objects.filter(user=request.user, equipment=equipment, returned_on__isnull=True).first()

    if not record:
        messages.error(request, "No active borrow record found for this equipment.")
        return redirect('equipment_list')

    record.returned_on = timezone.now()
    record.save()

    equipment.quantity += 1
    equipment.save()

    messages.success(request, f"You have returned {equipment.name}.")
    return redirect('equipment_list')
