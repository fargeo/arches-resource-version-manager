import logging

from arches.app.models import models
from arches.app.models.resource import Resource

from arches_resource_version_manager.models import VersionedResource

logger = logging.getLogger(__name__)


def archive_and_copy_draft(resource_group_id: str, user) -> Resource:
    """
    Archive the current editable Draft by cloning it with a Retired lifecycle
    state, recording the clone in VersionedResource, then returning the original
    draft resource for further mutation.
    """
    try:
        current_version = VersionedResource.objects.get(
            resource_group_id=resource_group_id,
            editable=True,
        )
    except VersionedResource.DoesNotExist:
        raise ValueError(
            f"No editable Draft VersionedResource found for {resource_group_id!r}."
        )

    draft_resource = models.Resource.objects.get(pk=current_version.pk)
    draft_clone = draft_resource.copy()
    draft_clone.resource_instance_lifecycle_state = (
        models.ResourceInstanceLifecycleState.objects.get(name="Retired")
    )
    draft_clone.save(user=user)

    VersionedResource.objects.create(
        resourceinstance_id=draft_clone.resourceinstanceid,
        resource_group_id=resource_group_id,
        major_version=current_version.major_version,
        minor_version=current_version.minor_version,
        payload=current_version.payload,
        editable=False,
    )

    return draft_resource


def register_new_draft(resource: Resource, resource_group_id: str, payload: dict) -> VersionedResource:
    """Record a newly created resource as its first editable Draft version."""
    return VersionedResource.objects.create(
        resourceinstance_id=resource.resourceinstanceid,
        resource_group_id=resource_group_id,
        major_version=1,
        minor_version=0,
        payload=payload,
        editable=True,
    )


def finalize_draft(resource_group_id: str, user, major_version, payload: dict) -> Resource:
    """
    Promote the current Draft to a new Final (Active) version.

    - Retires the existing Final (if any) by setting its lifecycle state to Retired.
    - Clones the updated Draft as the new Final with lifecycle state Active.
    - Creates a new VersionedResource record for the Final.

    Returns the new Final resource.
    """
    try:
        current_final_versioned = VersionedResource.objects.get(
            resource_group_id=resource_group_id,
            resourceinstance__resource_instance_lifecycle_state__name="Active",
        )
    except VersionedResource.DoesNotExist:
        current_final_versioned = None

    if current_final_versioned:
        current_final_resource = models.Resource.objects.get(pk=current_final_versioned.pk)
        current_final_resource.resource_instance_lifecycle_state = (
            models.ResourceInstanceLifecycleState.objects.get(name="Retired")
        )
        current_final_resource.save(user=user)

    try:
        draft_versioned = VersionedResource.objects.get(
            resource_group_id=resource_group_id,
            editable=True,
        )
    except VersionedResource.DoesNotExist:
        raise ValueError(
            f"No editable Draft VersionedResource found for {resource_group_id!r}."
        )

    draft_resource = models.Resource.objects.get(pk=draft_versioned.pk)
    final_resource = draft_resource.copy()
    final_resource.resource_instance_lifecycle_state = (
        models.ResourceInstanceLifecycleState.objects.get(name="Active")
    )
    final_resource.save(user=user)

    VersionedResource.objects.create(
        resourceinstance_id=final_resource.resourceinstanceid,
        resource_group_id=resource_group_id,
        major_version=major_version,
        minor_version=0,
        payload=payload,
        editable=False,
    )

    return final_resource
