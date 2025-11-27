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


#home 
def home(request):
    equipments = Equipment.objects.all()[:5]
    return render(request, 'equipment/home.html', {'equipments': equipments})

#registering new users/saff/admin
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

#login page
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

#renders dash boad after login/register
@login_required
def dashboard(request):
    if request.user.role == 'Admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'Staff':
        return redirect('staff_dashboard')
    return redirect('viewer_dashboard')

#this is used by user/viwer to request equipmnet
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


#admin dashboard
@admin_required
def admin_dashboard(request):
    equipments = Equipment.objects.all()
    suppliers = Supplier.objects.all()

    # Existing alerts from Alert table
    db_alerts = Alert.objects.filter(is_active=True)  # Only DB alerts

    # Generate low-stock alerts dynamically
    LOW_STOCK_THRESHOLD = 2
    low_stock_equipments = [eq for eq in equipments if eq.quantity < LOW_STOCK_THRESHOLD]

    borrowed_count = UsageRecord.objects.filter(returned_on__isnull=True).count()
    category_data = Equipment.objects.values('category').annotate(count=Count('id'))

    context = {
        'equipments': equipments,
        'supplier_count': suppliers.count(),
        'equipment_count': equipments.count(),
        'borrowed_count': borrowed_count,
        'alert_count': db_alerts.count(),
        'db_alerts': db_alerts,            # Only DB alerts for resolving
        'low_stock_equipments': low_stock_equipments,  # Low stock alerts
        'categories': [c['category'] for c in category_data],
        'counts': [c['count'] for c in category_data],
    }
    return render(request, 'equipment/admin_dashboard.html', context)


# Resolve active alerts (discard or add back)
@login_required
@admin_required
def resolve_alert(request, alert_id, action):
    """
    Handle active alerts from DB:
    - 'discard': remove the equipment and mark alert inactive
    - 'add_back': restore equipment quantity and mark alert inactive
    """
    alert = get_object_or_404(Alert, id=alert_id, is_active=True)
    equipment = alert.equipment

    if action == "discard":
        equipment.delete()
        alert.is_active = False
        alert.save()
        messages.success(request, f"{equipment.name} discarded and alert resolved.")
    elif action == "add_back":
        equipment.quantity += 1
        equipment.save()
        alert.is_active = False
        alert.save()
        messages.success(request, f"{equipment.name} added back to inventory and alert resolved.")
    else:
        messages.error(request, "Invalid action.")

    return redirect("admin_dashboard")



#admin only can add suppliers
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


#staff dashboard - approve requests, accept back rquipments and sends alret to admin in case of damage or wishlist
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
        days_overdue=F('due_date') - today
    )

    # Approving or rejecting equipment requests
    if request.method == "POST" and "request_id" in request.POST:
        action = request.POST.get("action")
        req_id = request.POST.get("request_id")
        req = get_object_or_404(EquipmentRequest, id=req_id)
        equipment = req.equipment

        if action == "approve":
            due_date = request.POST.get("due_date")
            if not due_date:
                messages.error(request, "Due date required.")
                return redirect("staff_dashboard")
            if req.quantity > equipment.quantity:
                messages.error(request, "Not enough stock available.")
                return redirect("staff_dashboard")

            equipment.quantity -= req.quantity
            equipment.save()

            UsageRecord.objects.create(
                user=req.user,
                equipment=equipment,
                quantity_used=req.quantity,
                borrowed_on=today,
                due_date=due_date,
                purpose=req.purpose or "Requested through dashboard",
                approved_by=request.user
            )

            req.status = "approved"
            req.processed_at = timezone.now()
            req.save()
            messages.success(request, f"Approved request for {equipment.name}")

        elif action == "reject":
            req.status = "rejected"
            req.processed_at = timezone.now()
            req.save()
            messages.info(request, "Request rejected.")

        return redirect("staff_dashboard")

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



#viewer dashboard with search and filters
@login_required
@viewer_allowed
def viewer_dashboard(request):
    equipments = Equipment.objects.all()
    categories = Equipment.objects.values_list('category', flat=True).distinct()
    locations = Equipment.objects.values_list('location', flat=True).distinct()

    # Get filters from GET request
    search_name = request.GET.get('name', '')
    category_filter = request.GET.get('category', '')
    location_filter = request.GET.get('location', '')

    if search_name:
        equipments = equipments.filter(name__icontains=search_name)
    if category_filter:
        equipments = equipments.filter(category=category_filter)
    if location_filter:
        equipments = equipments.filter(location=location_filter)

    form = EquipmentRequestForm()
    context = {
        'equipments': equipments,
        'categories': categories,
        'locations': locations,
        'search_name': search_name,
        'category_filter': category_filter,
        'location_filter': location_filter,
        'form': form,
    }
    return render(request, 'equipment/viewer_dashboard.html', context)


def no_permission(request):
    return render(request, 'equipment/no_permission.html')

#adding equipment by admin
@login_required
@admin_required
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
def admin_borrowers(request):
    # Show all records (both returned and unreturned)
    borrowers = UsageRecord.objects.all().order_by('-borrowed_on')

    # Optional filters
    user_filter = request.GET.get('user')
    equipment_filter = request.GET.get('equipment')

    if user_filter:
        borrowers = borrowers.filter(user__username__icontains=user_filter)
    if equipment_filter:
        borrowers = borrowers.filter(equipment__name__icontains=equipment_filter)

    return render(request, "equipment/admin_borrowers.html", {
        "borrowers": borrowers
    })



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


#returning equipment
@login_required
@staff_required
def return_equipment(request, id):
    record = get_object_or_404(UsageRecord, id=id)
    equipment = record.equipment

    if request.method == "POST":
        if not record.collected_by:
            # Mark as collected
            record.collected_by = request.user
            messages.success(request, f"{equipment.name} collected successfully!")
        else:
            # Handle return
            record.returned_on = timezone.now().date()
            record.is_damaged = "is_damaged" in request.POST
            record.damage_report = request.POST.get("damage_report", "")
            record.penalty_amount = request.POST.get("penalty_amount", 0)

            # Update inventory
            if record.is_damaged:
                equipment.quantity -= record.quantity_used

                # CREATE ALERT FOR DAMAGE
                Alert.objects.create(
                    equipment=equipment,
                    alert_type="Damaged",
                    description=record.damage_report or "Damage reported during return",
                    is_active=True
                )
            else:
                equipment.quantity += record.quantity_used

            # CREATE ALERT IF STOCK LOW
            if equipment.quantity <= 2:
                Alert.objects.create(
                    equipment=equipment,
                    alert_type="Low Stock",
                    description=f"Only {equipment.quantity} units left",
                    is_active=True
                )

            messages.success(request, f"{equipment.name} returned successfully!")

        record.save()
        equipment.save()
        return redirect('staff_dashboard')

    return render(request, "equipment/return_equipment.html", {"record": record})



#view all users to admin
@admin_required
def admin_users(request):
    users = User.objects.all().order_by('role')
    return render(request, 'equipment/admin_users.html', {'users': users})

#admin to view all users
@admin_required
def admin_staff_list(request):
    staff = User.objects.filter(role="Staff")
    return render(request, 'equipment/admin_staff_list.html', {'staff': staff})

#admin has to aprove staff
#todo show only staff there
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
