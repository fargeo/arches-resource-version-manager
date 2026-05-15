from __future__ import annotations

from typing import Optional

from django.db import models
from django.db.models.deletion import CASCADE

from arches.app.models.models import ResourceInstance
from arches.app.models.resource import Resource


class VersionedResourceManager(models.Manager):
    def get_current_by_lifecycle_state(
        self, resource_group_id: str, lifecycle_state: str
    ) -> Optional[VersionedResource]:
        try:
            return self.get(
                resource_group_id=resource_group_id,
                resourceinstance__resource_instance_lifecycle_state__name=lifecycle_state,
            )
        except self.model.DoesNotExist:
            return None

    def get_current_draft(self, resource_group_id: str) -> VersionedResource:
        """Raises VersionedResource.DoesNotExist if no Draft exists."""
        return self.get_current_by_lifecycle_state(resource_group_id, "Draft")

    def get_current_final(self, resource_group_id: str) -> Optional[VersionedResource]:
        return self.get_current_by_lifecycle_state(resource_group_id, "Active")


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

    class Meta:
        managed = True
        db_table = "versioned_resource"
