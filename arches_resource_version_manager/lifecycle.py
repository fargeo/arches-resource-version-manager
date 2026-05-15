import logging

from arches.app.models import models
from arches.app.models.resource import Resource

from arches_resource_version_manager.models import VersionedResource

logger = logging.getLogger(__name__)


def get_current_draft(resource_group_id: str) -> Resource:
    """Return the current editable Draft for the given resource group, or raise VersionedResource.DoesNotExist if not found."""
    return get_current_by_lifecycle_state(resource_group_id, lifecycle_state="Draft")


def get_current_final(resource_group_id: str) -> Resource:
    """Return the current Final (Active) version for the given resource group, or None if not found."""
    return get_current_by_lifecycle_state(resource_group_id, lifecycle_state="Active")


def get_current_by_lifecycle_state(
    resource_group_id: str, lifecycle_state: str
) -> Resource:
    """Return the current version for the given resource group and lifecycle state, or None if not found."""
    try:
        return VersionedResource.objects.get(
            resource_group_id=resource_group_id,
            resourceinstance__resource_instance_lifecycle_state__name=lifecycle_state,
        )
    except VersionedResource.DoesNotExist:
        return None


def archive_copy_of_current_draft(resource_group_id: str, user) -> Resource:
    """
    Archive the current editable Draft by cloning it with a Retired lifecycle
    state, recording the clone in VersionedResource, then returning the new
    archived VersionedResource.
    """
    draft_versioned_resource = get_current_draft(resource_group_id)

    draft_resource = models.Resource.objects.get(pk=draft_versioned_resource.pk)

    draft_resource_copy = draft_resource.copy()
    draft_resource_copy.resource_instance_lifecycle_state = (
        models.ResourceInstanceLifecycleState.objects.get(name="Retired")
    )
    draft_resource_copy.save(user=user)

    return VersionedResource.objects.create(
        resourceinstance_id=draft_resource_copy.resourceinstanceid,
        resource_group_id=resource_group_id,
        major_version=draft_versioned_resource.major_version,
        minor_version=draft_versioned_resource.minor_version,
        payload=draft_versioned_resource.payload,
    )


def register_new_draft(
    resource: Resource, resource_group_id: str, payload: dict
) -> VersionedResource:
    """Record a newly created resource as its first editable Draft version."""
    return VersionedResource.objects.create(
        resourceinstance_id=resource.resourceinstanceid,
        resource_group_id=resource_group_id,
        major_version=1,
        minor_version=0,
        payload=payload,
    )


def finalize_draft(
    resource_group_id: str, user, major_version, payload: dict
) -> Resource:
    """
    Promote the current Draft to a new Final (Active) version.

    - Retires the existing Final (if any) by setting its lifecycle state to Retired.
    - Clones the updated Draft as the new Final with lifecycle state Active.
    - Creates a new VersionedResource record for the Final.

    Returns the new Final resource.
    """
    current_final = get_current_final(resource_group_id)
    current_draft = get_current_draft(resource_group_id)

    if current_final:
        current_final_resource = models.Resource.objects.get(pk=current_final.pk)
        current_final_resource.resource_instance_lifecycle_state = (
            models.ResourceInstanceLifecycleState.objects.get(name="Retired")
        )
        current_final_resource.save(user=user)

    draft_resource = models.Resource.objects.get(pk=current_draft.pk)
    final_resource = draft_resource.copy()
    final_resource.resource_instance_lifecycle_state = (
        models.ResourceInstanceLifecycleState.objects.get(name="Active")
    )
    final_resource.save(user=user)

    return VersionedResource.objects.create(
        resourceinstance_id=final_resource.resourceinstanceid,
        resource_group_id=resource_group_id,
        major_version=major_version,
        minor_version=0,
        payload=payload,
    )
