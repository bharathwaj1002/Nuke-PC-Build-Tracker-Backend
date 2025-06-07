from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

# Define user roles
ROLE_CHOICES = [
    ('Sales Team', 'Sales Team'),
    ('Service Team', 'Service Team'),
    ('Supervisor', 'Supervisor'),
    ('Hardware Engineer TL', 'Hardware Engineer TL'),
    ('Hardware Engineer Team', 'Hardware Engineer Team'),
    ('Accounts Team', 'Accounts Team'),
]

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError("The Email address must be set")
        if not role:
            raise ValueError("The Role must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, role="Supervisor", **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email=email, password=password, role=role, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Build(models.Model):
    id = models.IntegerField(primary_key=True)
    STATUS_CHOICES = [
        ('Components Pending', 'Components Pending'),
        ('Components Assigned', 'Components Assigned'),
        ('Build Started', 'Build Started'),
        ('Build Completed', 'Build Completed'),
        ('Testing Started', 'Testing Started'),
        ('Test Completed', 'Test Completed'),
        ('Ready for Shipment', 'Ready for Shipment'),
        ('Shipped', 'Shipped'),
    ]
    customerName = models.CharField(max_length=100)
    mobileNumber = models.CharField(max_length=15)
    buildType = models.CharField(max_length=20, choices=[('Offer', 'Offer'), ('Normal', 'Normal')])
    deliveryType = models.CharField(max_length=20, choices=[('In-Person', 'In-Person'), ('Shipment', 'Shipment')])
    location = models.CharField(max_length=100)
    qualityCheckBy = models.CharField(max_length=100, null=True, blank=True)  # <-- NEW
    qualityCheckDate = models.DateTimeField(null=True, blank=True)
    eta = models.DateField(null=True, blank=True)
    deadline = models.DateField()
    orderDate = models.DateField()
    enquiryId = models.CharField(max_length=50)
    paymentDone = models.DecimalField(max_digits=10, decimal_places=2)
    dateOfInitialPayment = models.DateField(null=True, blank=True)
    dateOfFinalPayment = models.DateField(null=True, blank=True)
    totalAmount = models.DecimalField(max_digits=10, decimal_places=2)
    balancePayment = models.DecimalField(max_digits=10, decimal_places=2)
    adminName = models.CharField(max_length=100)
    builder = models.CharField(max_length=100, null=True, blank=True)
    tester = models.CharField(max_length=100, null=True, blank=True)
    currentStage = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Components Pending')
    status_updater = models.CharField(max_length=100, null=True, blank=True)
    builderAssignedDate = models.DateTimeField(null=True, blank=True)
    testerAssignedDate = models.DateTimeField(null=True, blank=True)
    shipmentStatus = models.CharField(max_length=50, null=True, default="Pending", blank=True, choices=[
        ('Pending', 'Pending'),
        ('In Transit', 'In Transit'),
        ('Delivered', 'Delivered')])
    trackingNumber = models.CharField(max_length=100, null=True, blank=True)
    @property
    def paymentStatus(self):
        if self.paymentDone >= self.totalAmount:
            return "Fully Paid"
        elif self.paymentDone > 0:
            return "Partial"
        else:
            return "Completed"
    @property
    def buildCompletedOnSameDay(self):
        return self.builderAssignedDate == self.statusLog.status == "Build Completed" and self.statusLog.created_at.date()
    
    @property
    def qualityCheckCompleted(self):
        return self.qualityCheckBy is not None
    
    @property
    def valid_builder_assigned_date(self):
        if self.builder and self.builderAssignedDate:
            return self.builderAssignedDate
        return None

    @property
    def valid_tester_assigned_date(self):
        if self.tester and self.testerAssignedDate:
            return self.testerAssignedDate
        return None
    
    def __str__(self):
        return f"{self.customerName} - {self.enquiryId} ({self.currentStage})"
class Component(models.Model):
    build = models.ForeignKey(Build, on_delete=models.CASCADE, related_name='components')
    price = models.IntegerField()
    name = models.CharField(max_length=100)
    serialNumber = models.CharField(max_length=100, null=True, blank=True)
    eta = models.DateField(null=True, blank=True)


    @property
    def available(self):
        return bool(self.serialNumber)

    def __str__(self):
        return f"{self.name} - {self.build.customerName} ({self.build.enquiryId})"
class StatusLog(models.Model):
    build = models.ForeignKey(Build, on_delete=models.CASCADE, related_name='status_logs')
    status = models.CharField(max_length=50)
    updated_by = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)
    
    # Optional additions
    action = models.CharField(max_length=10, choices=[('advance', 'Advance'), ('rollback', 'Rollback')], null=True, blank=True)
    role = models.CharField(max_length=100, null=True, blank=True)
    rollback_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.build.customerName} - {self.status} by {self.updated_by} on {self.timestamp}"


class Checklist(models.Model):
    build = models.OneToOneField(Build, on_delete=models.CASCADE, related_name='checklist')

    chipsetDrivers = models.TextField()
    graphicsDrivers = models.TextField()
    biosFirmwareVersion = models.TextField()
    networkDrivers = models.TextField()
    wifi = models.TextField()
    bluetooth = models.TextField()
    storagePartitioning = models.TextField()
    lanDetection = models.TextField()
    usbDetection = models.TextField()
    headphone = models.TextField()
    adminName = models.TextField()
    resizableBar = models.TextField()
    ramXmpProfile = models.TextField()
    prime95Test = models.TextField()
    operatingSystem = models.TextField()
    antivirusActivation = models.TextField()
    basicSoftwareInstallation = models.TextField()
    cinebenchR23SingleCoreStock = models.TextField()
    cinebenchR23MulticoreStock = models.TextField()
    cpuTemperatureIdleLoadStress = models.TextField()
    gpuTemperatureIdleLoadStress = models.TextField()
    game1AvgFps = models.TextField()
    game2AvgFps = models.TextField()
    premiereRenderTime = models.TextField()
    dateOfBenchmark = models.DateField()
    buildBy = models.TextField()
    testedBy = models.TextField()

    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Checklist for Build {self.build.id}"

class InvoiceStatus(models.Model):
    build = models.OneToOneField(Build, on_delete=models.CASCADE, related_name='invoice_status')
    invoice_raised = models.BooleanField(default=False)
    sales_order_raised = models.BooleanField(default=False)
