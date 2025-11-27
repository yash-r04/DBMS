from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),#does not work
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),#perfect
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('viewer-dashboard/', views.viewer_dashboard, name='viewer_dashboard'),
    path('no-permission/', views.no_permission, name='no_permission'),

    # Equipment Views
    path('equipments/', views.equipment_list, name='equipment_list'),
    path('equipment/<int:id>/', views.equipment_detail, name='equipment_detail'),
    path('add-equipment/', views.add_equipment, name='add_equipment'),
    path('equipment/<int:id>/edit/', views.equipment_edit, name='equipment_edit'),
    path('equipment/<int:id>/delete/', views.equipment_delete, name='equipment_delete'),

    path('suppliers/', views.supplier_list, name='supplier_list'),#works
    path('add-supplier/', views.add_supplier, name='add_supplier'),#works


    # Borrow / Return
    #path('borrow/<int:id>/', views.borrow_equipment, name='borrow_equipment'),
    path('return/<int:id>/', views.return_equipment, name='return_equipment'),
    # urls.py
    path('request-equipment/', views.request_equipment, name='request_equipment'),
    # Admin user management
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('admin-dashboard/staff/', views.admin_staff_list, name='admin_staff_list'),
    path('admin-dashboard/approve-staff/<int:id>/', views.approve_staff, name='approve_staff'),
    path('admin-dashboard/borrowers/', views.admin_borrowers, name='admin_borrowers'),


]
