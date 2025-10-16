import uuid

from django.db import models


class ScanResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='scans/')
    text = models.TextField(blank=True)
    structured_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Scan {self.id} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scan Result'
        verbose_name_plural = 'Scan Results'
