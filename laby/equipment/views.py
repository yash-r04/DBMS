from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.db.models import F, Count
from django.db import models

from .models import (
    Equipment, Supplier, UsageRecord, Alert, User, EquipmentRequest
)
from .forms import (
    RegisterForm, EquipmentForm, SupplierForm, EquipmentRequestForm
)
from .decorators import admin_required, staff_required, viewer_allowed


# ============================================================
# HOME + AUTH
# ============================================================

def home(request):
    equipments = Equipment.objects.all()[:5]
    return render(request, 'equipment/home.html', {'equipments': equipments})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            if user.role == 'Admin':
                return redirect('admin_dashboard')
            elif user.role == 'Staff':
                return redirect('staff_dashboard')
            else:
                return redirect('viewer_dashboard')

        messages.error(request, "Please correct errors below.")
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

        messages.error(request, "Invalid credentials.")

    return render(request, 'equipment/login.html')


@login_required
def dashboard(request):
    if request.user.role == 'Admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'Staff':
        return redirect('staff_dashboard')
    return redirect('viewer_dashboard')


# ============================================================
# VIEWER: REQUEST EQUIPMENT (ONE FINAL VERSION)
# ============================================================

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


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@admin_required
def admin_dashboard(request):
    equipments = Equipment.objects.all()
    suppliers = Supplier.objects.all()
    alerts = Alert.objects.all()

    borrowed_count = UsageRecord.objects.filter(returned_on__isnull=True).count()

    category_data = Equipment.objects.values('category').annotate(count=Count('id'))

    context = {
        'equipments': equipments,
        'supplier_count': suppliers.count(),
        'equipment_count': equipments.count(),
        'borrowed_count': borrowed_count,
        'alert_count': alerts.count(),
        'categories': [c['category'] for c in category_data],
        'counts': [c['count'] for c in category_data],
    }
    return render(request, 'equipment/admin_dashboard.html', context)


# ============================================================
# SUPPLIERS (Admin only)
# ============================================================

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
            messages.success(request, "Supplier added!")
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'equipment/add_supplier.html', {'form': form})


# ============================================================
# STAFF DASHBOARD (handles approval + borrowing display)
# ============================================================

@login_required
@staff_required
def staff_dashboard(request):

    today = timezone.now().date()

    borrowed_records = UsageRecord.objects.filter(returned_on__isnull=True)
    borrowed_count = borrowed_records.count()

    equipment_count = Equipment.objects.count()
    alert_count = Alert.objects.filter(is_active=True).count()

    overdue_records = UsageRecord.objects.filter(
        returned_on__isnull=True,
        due_date__lt=today
    ).annotate(
        days_overdue=timezone.now().date() - F('due_date')
    )

    # =====================================================
    # HANDLE APPROVE / REJECT
    # =====================================================
    if request.method == "POST":
        action = request.POST.get("action")
        req_id = request.POST.get("request_id")

        try:
            req = EquipmentRequest.objects.get(id=req_id)
        except EquipmentRequest.DoesNotExist:
            messages.error(request, "Request not found.")
            return redirect("staff_dashboard")

        equipment = req.equipment

        # ---------- APPROVE ----------
        if action == "approve":
            due_date = request.POST.get("due_date")

            if not due_date:
                messages.error(request, "Due date required.")
                return redirect("staff_dashboard")

            if req.quantity > equipment.quantity:
                messages.error(request, "Not enough stock available.")
                return redirect("staff_dashboard")

            # Update quantity
            equipment.quantity -= req.quantity
            equipment.save()

            # Create usage record
            UsageRecord.objects.create(
                user=req.user,
                equipment=equipment,
                quantity_used=req.quantity,
                borrowed_on=today,
                due_date=due_date,
                purpose=req.purpose or "Requested through dashboard",
                returned_on=None
            )

            req.status = "approved"
            req.processed_at = timezone.now()
            req.save()

            messages.success(request, f"Approved request for {equipment.name}")

        # ---------- REJECT ----------
        elif action == "reject":
            req.status = "rejected"
            req.processed_at = timezone.now()
            req.save()
            messages.info(request, "Request rejected.")

        return redirect("staff_dashboard")

    # =====================================================
    # Pending (only pending)
    # =====================================================
    requests_list = EquipmentRequest.objects.filter(status='pending')

    context = {
        "borrowed_records": borrowed_records,
        "borrowed_count": borrowed_count,
        "equipment_count": equipment_count,
        "alert_count": alert_count,
        "overdue_records": overdue_records,
        "requests": requests_list,
        "today": today,
    }
    return render(request, "equipment/staff_dashboard.html", context)


# ============================================================
# VIEWER DASHBOARD
# ============================================================

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

# ============================================================
# EQUIPMENT CRUD
# ============================================================

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
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('equipment_list')
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
            messages.success(request, "Equipment updated.")
            return redirect('equipment_list')
    else:
        form = EquipmentForm(instance=equipment)
    return render(request, 'equipment/equipment_form.html', {'form': form})


@admin_required
def equipment_delete(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, "Equipment deleted.")
        return redirect('equipment_list')
    return render(request, 'equipment/equipment_confirm_delete.html', {'equipment': equipment})


# ============================================================
# RETURN EQUIPMENT
# ============================================================

@login_required
@staff_required
def return_equipment(request, id):
    record = get_object_or_404(UsageRecord, id=id)
    equipment = record.equipment

    if request.method == "POST":
        record.returned_on = timezone.now().date()
        record.save()

        equipment.quantity += record.quantity_used
        equipment.save()

        messages.success(request, f"{equipment.name} returned.")
        return redirect('staff_dashboard')

    return render(request, "equipment/return_equipment.html", {"record": record})


# -----------------------------
# ADMIN: VIEW ALL USERS
# -----------------------------
@admin_required
def admin_users(request):
    users = User.objects.all().order_by('role')
    return render(request, 'equipment/admin_users.html', {'users': users})


# -----------------------------
# ADMIN: VIEW STAFF ONLY
# -----------------------------
@admin_required
def admin_staff_list(request):
    staff = User.objects.filter(role="Staff")
    return render(request, 'equipment/admin_staff_list.html', {'staff': staff})


# -----------------------------
# ADMIN: APPROVE STAFF USER
# -----------------------------
@admin_required
def approve_staff(request, id):
    staff_user = get_object_or_404(User, id=id)

    if staff_user.role != "Staff":
        messages.error(request, "User is not a staff member.")
        return redirect("admin_staff_list")

    staff_user.is_approved = True
    staff_user.save()

    messages.success(request, f"{staff_user.username} approved as staff!")
    return redirect("admin_staff_list")


# -----------------------------
# ADMIN: VIEW BORROWERS
# -----------------------------
@admin_required
def admin_borrowers(request):
    borrowers = UsageRecord.objects.filter(returned_on__isnull=True)
    return render(request, "equipment/admin_borrowers.html", {
        "borrowers": borrowers
    })
