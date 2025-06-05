from rest_framework import serializers
from .models import Build, Component, StatusLog, Checklist, InvoiceStatus

class ComponentSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()

    class Meta:
        model = Component
        exclude = ['build']

    def get_available(self, obj):
        return obj.available

class BuildSerializer(serializers.ModelSerializer):
    components = ComponentSerializer(many=True)
    paymentStatus = serializers.SerializerMethodField()
    qualityCheckCompleted = serializers.SerializerMethodField()
    
    # New read-only fields for conditional dates
    valid_builder_assigned_date = serializers.SerializerMethodField()
    valid_tester_assigned_date = serializers.SerializerMethodField()

    class Meta:
        model = Build
        fields = '__all__'  # or list all fields explicitly if preferred
        # Alternatively: 
        # fields = [ ...existing fields..., 'valid_builder_assigned_date', 'valid_tester_assigned_date' ]

    def create(self, validated_data):
        components_data = validated_data.pop('components', [])
        build = Build.objects.create(**validated_data)
        for comp_data in components_data:
            Component.objects.create(build=build, **comp_data)
        return build

    def update(self, instance, validated_data):
        components_data = validated_data.pop('components', None)

        # Update non-component fields
        instance = super().update(instance, validated_data)

        if components_data is not None:
            instance.components.all().delete()
            for comp_data in components_data:
                Component.objects.create(build=instance, **comp_data)

        return instance

    def get_paymentStatus(self, obj):
        return obj.paymentStatus

    def get_qualityCheckCompleted(self, obj):
        return obj.qualityCheckCompleted

    def get_valid_builder_assigned_date(self, obj):
        # Return builderAssignedDate only if builder assigned
        if obj.builder and obj.builderAssignedDate:
            return obj.builderAssignedDate
        return None

    def get_valid_tester_assigned_date(self, obj):
        # Return testerAssignedDate only if tester assigned
        if obj.tester and obj.testerAssignedDate:
            return obj.testerAssignedDate
        return None

class StatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusLog
        fields = '__all__'

class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = '__all__'

class InvoiceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceStatus
        fields = '__all__'
