from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('builds/', views.build_list_create, name='build-list'),
    path('builds/<int:pk>/', views.build_detail, name='build-detail'),

    path('components/', views.component_list_create, name='component-list'),
    path('components/<int:pk>/', views.component_detail, name='component-detail'),

    path('status-logs/', views.status_log_list_create, name='status-log-list'),
    path('status-logs/<int:build_id>', views.update_build_stage, name='status-log-update'),
    path('get-status-log/<int:build_id>', views.get_status_log, name='get-status-log'),

    path('checklists/', views.checklist_list_create, name='checklist-list'),

    path('invoice-statuses/', views.invoice_status_list_create, name='invoice-status-list'),
    
    path('login/', views.login, name='login'),
    path('get-user-role/', views.get_user_role, name='get-user-role'),
    # Access Token
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]