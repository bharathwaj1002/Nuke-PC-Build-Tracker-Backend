from django.urls import path
from . import views

urlpatterns = [
    path('builds/', views.build_list_create, name='build-list'),
    path('builds/<int:pk>/', views.build_detail, name='build-detail'),

    path('components/', views.component_list_create, name='component-list'),
    path('components/<int:pk>/', views.component_detail, name='component-detail'),

    path('status-logs/', views.status_log_list_create, name='status-log-list'),

    path('checklists/', views.checklist_list_create, name='checklist-list'),

    path('invoice-statuses/', views.invoice_status_list_create, name='invoice-status-list'),
]