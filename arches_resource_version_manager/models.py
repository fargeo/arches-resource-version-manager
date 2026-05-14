from django.db import models
from django.db.models.deletion import CASCADE

from arches.app.models.models import ResourceInstance
from arches.app.models.resource import Resource


class VersionedResourceManager(models.Manager):
    def get_current_draft(self, resource_group_id: str) -> Resource:
        versioned = self.get(
            resource_group_id=resource_group_id,
            editable=True,
        )
        return Resource.objects.get(pk=versioned.pk)

    def get_current_final(self, resource_group_id: str) -> Resource:
        versioned = self.get(
            resource_group_id=resource_group_id,
            resourceinstance__resource_instance_lifecycle_state__name="Active",
        )
        return Resource.objects.get(pk=versioned.pk)


class VersionedResource(models.Model):
    objects = VersionedResourceManager()

    resourceinstance = models.OneToOneField(
        ResourceInstance,
        on_delete=CASCADE,
        primary_key=True,
    )
    resource_group_id = models.CharField(max_length=255)
    version = models.CharField(max_length=255, blank=True, null=True)
    payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    editable = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = "versioned_resource"
