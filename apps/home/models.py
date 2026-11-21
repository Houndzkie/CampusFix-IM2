import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, school_id, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not school_id:
            raise ValueError('The School ID field must be set')
        email = self.normalize_email(email)
        user = self.model(school_id=school_id, email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, school_id, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(school_id, email, full_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("faculty", "Faculty"),
        ("maintenance_staff", "Maintenance Staff"),
        ("admin", "Administrator"),
    )
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'school_id'
    REQUIRED_FIELDS = ['email', 'full_name']

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.full_name

class UserProfile(models.Model):
    profile_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    profile_photo_url = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'

class Building(models.Model):
    building_id = models.AutoField(primary_key=True)
    building_code = models.CharField(max_length=10, unique=True)
    building_name = models.CharField(max_length=100)
    total_floors = models.IntegerField()

    class Meta:
        db_table = 'building'

    def __str__(self):
        return self.building_name

class Room(models.Model):
    room_id = models.AutoField(primary_key=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    room_name = models.CharField(max_length=50)
    floor_number = models.IntegerField()
    room_type = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = 'room'

    def __str__(self):
        return f"{self.room_name} - {self.building.building_name}"

class RepairRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("finished", "Finished"),
    )
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_requests')
    assigned_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    room = models.ForeignKey(Room, on_delete=models.RESTRICT, related_name='requests')
    title = models.CharField(max_length=100)
    description = models.TextField()
    priority = models.CharField(max_length=10)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'repair_request'

    def __str__(self):
        return self.title

class RequestPhoto(models.Model):
    photo_id = models.BigAutoField(primary_key=True)
    request = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name='photos')
    photo_url = models.TextField()
    photo_type = models.CharField(max_length=10)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'request_photo'

class RequestComment(models.Model):
    comment_id = models.BigAutoField(primary_key=True)
    request = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'request_comment'

class StatusHistory(models.Model):
    history_id = models.BigAutoField(primary_key=True)
    request = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name='status_history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='status_changes')
    old_status = models.CharField(max_length=15, null=True, blank=True)
    new_status = models.CharField(max_length=15)
    remarks = models.TextField(null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'status_history'

class Notification(models.Model):
    notification_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    request = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification'
