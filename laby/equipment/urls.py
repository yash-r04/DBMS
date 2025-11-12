from django.urls import path
from . import views

urlpatterns = [
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/<int:id>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/add/', views.equipment_add, name='equipment_add'),
    path('equipment/<int:id>/edit/', views.equipment_edit, name='equipment_edit'),
    path('equipment/<int:id>/delete/', views.equipment_delete, name='equipment_delete'),
]
