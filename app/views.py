from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Build, Component, StatusLog, Checklist, InvoiceStatus
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    BuildSerializer, ComponentSerializer, StatusLogSerializer,
    ChecklistSerializer, InvoiceStatusSerializer
)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def build_list_create(request):
    if request.method == 'GET':
        builds = Build.objects.all().order_by('id')
        serialized_builds = []

        # Define the correct order of stages
        stage_order = [
            'Components Pending',
            'Components Assigned',
            'Build Started',
            'Build Completed',
            'Testing Started',
            'Test Completed',
            'Ready for Shipment',
            'Shipped'
        ]

        def stage_index(stage):
            try:
                return stage_order.index(stage)
            except ValueError:
                return -1

        for build in builds:
            build_data = BuildSerializer(build).data
            current_stage_idx = stage_index(build.currentStage)

            # Get latest successful advance logs for relevant stages
            build_completed_log = None
            test_completed_log = None

            if current_stage_idx >= stage_index("Build Completed"):
                build_completed_log = (
                    StatusLog.objects
                    .filter(build=build, status="Build Completed", action="advance")
                    .order_by('-timestamp')
                    .first()
                )

            if current_stage_idx >= stage_index("Test Completed"):
                test_completed_log = (
                    StatusLog.objects
                    .filter(build=build, status="Test Completed", action="advance")
                    .order_by('-timestamp')
                    .first()
                )

            # Add custom fields to serialized data
            build_data["buildCompletedDate"] = build_completed_log.timestamp if build_completed_log else None
            build_data["testCompletedDate"] = test_completed_log.timestamp if test_completed_log else None

            serialized_builds.append(build_data)

        return Response(serialized_builds)
    
    elif request.method == 'POST':
        serializer = BuildSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'DELETE'])
def build_detail(request, pk):
    try:
        build = Build.objects.get(pk=pk)
    except Build.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BuildSerializer(build)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = BuildSerializer(build, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        print(serializer.errors)
        print(request.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        build.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Repeat for other models
@api_view(['GET', 'POST'])
def component_list_create(request):
    if request.method == 'GET':
        components = Component.objects.all()
        serializer = ComponentSerializer(components, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ComponentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def component_detail(request, pk):
    try:
        component = Component.objects.get(pk=pk)
    except Component.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ComponentSerializer(component)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ComponentSerializer(component, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        component.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
def status_log_list_create(request):
    if request.method == 'GET':
        logs = StatusLog.objects.all()
        serializer = StatusLogSerializer(logs, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = StatusLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_status_log(request, build_id):
    if request.method == 'GET':
        logs = StatusLog.objects.filter(build_id=build_id)
        serializer = StatusLogSerializer(logs, many=True)
        return Response(serializer.data)

@api_view(['POST'])
def update_build_stage(request, build_id):
    try:
        build = Build.objects.get(pk=build_id)
    except Build.DoesNotExist:
        return Response({"error": "Build not found"}, status=status.HTTP_404_NOT_FOUND)

    data = request.data
    stage = data.get('stage')
    user = data.get('user')
    action = data.get('action')
    role = data.get('role')
    notes = data.get('notes', '')
    rollback_reason = data.get('rollbackReason', '')

    if not stage or not user:
        return Response({"error": "Missing 'stage' or 'user'"}, status=status.HTTP_400_BAD_REQUEST)

    # Update build stage
    build.currentStage = stage
    build.save()

    # Create status log
    StatusLog.objects.create(
        build=build,
        status=stage,
        updated_by=user,
        remarks=notes,
        action=action,
        role=role,
        rollback_reason=rollback_reason
    )

    return Response({"message": "Build stage updated and status log created"}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def checklist_list_create(request):
    if request.method == 'GET':
        checklists = Checklist.objects.all()
        serializer = ChecklistSerializer(checklists, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        build_id = request.data.get('build')

        if not build_id:
            return Response({"error": "Build ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            build = Build.objects.get(id=build_id)
        except Build.DoesNotExist:
            return Response({"error": "Build not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            checklist = Checklist.objects.get(build=build)
            # Update existing checklist
            serializer = ChecklistSerializer(checklist, data=request.data, partial=True)
        except Checklist.DoesNotExist:
            # Create new checklist
            serializer = ChecklistSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(build=build)  # Ensure the checklist is linked to the build
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_checklist(request, build_id):
    checklist = get_object_or_404(Checklist, build__id=build_id)
    serializer = ChecklistSerializer(checklist)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
def invoice_status_list_create(request):
    if request.method == 'GET':
        invoices = InvoiceStatus.objects.all()
        serializer = InvoiceStatusSerializer(invoices, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = InvoiceStatusSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['POST'])
@permission_classes([AllowAny])  # No authentication required for login
def login(request):
    email = request.data.get('email')
    email = email.lower()
    password = request.data.get('password')

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=400)
    
    try:

        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            })
        else:
            return Response({"error": "Invalid credentials"}, status=401)
    except User.DoesNotExist:
        return Response({"error": "User with this email does not exist"}, status=404)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_role(request):
    user = request.user
    if user:
        return Response({"role": user.role}, status=200)
    else:
        return Response({"error": "User not authenticated"}, status=401)