from django.db import models
from django.db.models import Q
from django.contrib.auth.models import Group


class Flavor(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cpu_cores = models.PositiveIntegerField()
    memory_mb = models.PositiveIntegerField()
    disk_gb = models.PositiveIntegerField()
    gpu_type = models.CharField(max_length=255)
    gpu_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ComputeNode(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cpu_cores = models.PositiveIntegerField()
    memory_mb = models.PositiveIntegerField()
    disk_gb = models.PositiveIntegerField()
    gpu_type = models.CharField(max_length=255)
    gpu_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FloatingIP(models.Model):
    ip_address = models.GenericIPAddressField(protocol='both', unique=True)
    virtual_machine = models.ForeignKey('VirtualMachine', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['virtual_machine'],
                condition=Q(virtual_machine__isnull=False),
                name='unique_virtual_machine'
            )
        ]


class Image(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Environment(models.Model):
    name = models.CharField(max_length=255)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('name', 'group')


class Key(models.Model):
    name = models.CharField(max_length=255)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    public_key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('name', 'environment')


class VirtualMachine(models.Model):
    STATE_CHOICES = [
        ('starting', 'STARTING'),
        ('started', 'STARTED'),
        ('failed', 'FAILED'),
        ('deleting', 'DELETING'),
    ]
    name = models.CharField(max_length=255)
    hypervisor_id = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=16, choices=STATE_CHOICES, default='starting')
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    flavor = models.ForeignKey(Flavor, on_delete=models.CASCADE)
    user_data = models.TextField(blank=True, null=True)
    callback_url = models.URLField(blank=True, null=True)
    compute_node = models.ForeignKey(ComputeNode, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('name', 'environment')


class VMKeyBinding(models.Model):
    virtual_machine = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)
    key = models.ForeignKey(Key, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('virtual_machine', 'key')


class VMLabel(models.Model):
    name = models.CharField(max_length=255)
    virtual_machine = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('virtual_machine', 'name')
