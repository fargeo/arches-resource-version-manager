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
        return versioned.resourceinstance

    def get_current_final(self, resource_group_id: str) -> Resource:
        versioned = self.get(
            resource_group_id=resource_group_id,
            resourceinstance__resource_instance_lifecycle_state__name="Active",
        ).select_related("resourceinstance")
        return versioned.resourceinstance


class VersionedResource(models.Model):
    objects = VersionedResourceManager()

    resourceinstance = models.OneToOneField(
        ResourceInstance,
        on_delete=CASCADE,
        primary_key=True,
    )
    resource_group_id = models.CharField(max_length=255)
    major_version = models.IntegerField(default=0)
    minor_version = models.IntegerField(default=0)
    payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    editable = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = "versioned_resource"
