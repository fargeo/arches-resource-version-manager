from django.db import models

from arches.app.models.models import ResourceInstance
from arches.app.models.resource import Resource


class ResourceVersionManager(models.Manager):
    def get_current_draft(self, resource_group_id: str) -> Resource:
        version = self.get(
            resource_group_id=resource_group_id,
            state=VersionedResource.DRAFT,
            editable=True,
        )
        return Resource.objects.get(resourceinstanceid=version.resourceinstanceid_id)

    def get_current_final(self, resource_group_id: str) -> Resource:
        version = self.get(
            resource_group_id=resource_group_id,
            state=VersionedResource.FINAL,
        )
        return Resource.objects.get(resourceinstanceid=version.resourceinstanceid_id)


class VersionedResource(models.Model):
    DRAFT = "draft"
    FINAL = "final"
    ARCHIVED = "archived"
    STATE_CHOICES = {
        DRAFT: "draft",
        FINAL: "final",
        ARCHIVED: "archived",
    }

    objects = ResourceVersionManager()

    resource_group_id = models.CharField(max_length=255)
    resourceinstanceid = models.ForeignKey(
        ResourceInstance,
        on_delete=models.CASCADE,
    )
    state = models.CharField(choices=STATE_CHOICES, default=DRAFT, max_length=50)
    version = models.CharField(max_length=255, blank=True, null=True)
    payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    editable = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = "resource_version"
