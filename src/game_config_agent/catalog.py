"""Resource master-data loading and name resolution."""

import json
from pathlib import Path

from .models import ResourceDefinition


class CatalogDataError(ValueError):
    """Raised when the snapshot or alias data is internally inconsistent."""


class ResourceCatalog:
    """Read-only view of resource truth from the official Unity snapshot."""

    def __init__(
        self,
        resources: list[ResourceDefinition],
        aliases: dict[str, str] | None = None,
    ) -> None:
        self._by_id: dict[str, ResourceDefinition] = {}
        self._by_name: dict[str, ResourceDefinition] = {}

        for resource in resources:
            if resource.id in self._by_id:
                raise CatalogDataError(f"Duplicate resource id: {resource.id}")
            name_key = self._normalize(resource.name)
            if name_key in self._by_name:
                raise CatalogDataError(f"Duplicate resource name: {resource.name}")
            self._by_id[resource.id] = resource
            self._by_name[name_key] = resource

        self._aliases: dict[str, ResourceDefinition] = {}
        for alias, resource_id in (aliases or {}).items():
            target = self._by_id.get(resource_id.upper())
            if target is None:
                raise CatalogDataError(
                    f"Alias {alias!r} points to unknown resource id {resource_id!r}"
                )
            alias_key = self._normalize(alias)
            existing = self._aliases.get(alias_key)
            if existing is not None and existing.id != target.id:
                raise CatalogDataError(f"Alias {alias!r} maps to multiple resources")
            self._aliases[alias_key] = target

    @classmethod
    def from_files(
        cls,
        snapshot_path: str | Path,
        aliases_path: str | Path | None = None,
    ) -> "ResourceCatalog":
        snapshot = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
        raw_resources = snapshot.get("resources")
        if not isinstance(raw_resources, list):
            raise CatalogDataError("Snapshot must contain a resources list")

        aliases: dict[str, str] = {}
        if aliases_path is not None:
            alias_document = json.loads(Path(aliases_path).read_text(encoding="utf-8"))
            raw_aliases = alias_document.get("aliases")
            if not isinstance(raw_aliases, dict):
                raise CatalogDataError("Alias file must contain an aliases object")
            aliases = {str(key): str(value) for key, value in raw_aliases.items()}

        resources = [ResourceDefinition.model_validate(item) for item in raw_resources]
        return cls(resources, aliases)

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().casefold()

    @property
    def resources(self) -> tuple[ResourceDefinition, ...]:
        return tuple(self._by_id.values())

    def resolve(self, value: str | None) -> ResourceDefinition | None:
        if value is None or not value.strip():
            return None

        normalized = self._normalize(value)
        by_id = self._by_id.get(value.strip().upper())
        if by_id is not None:
            return by_id
        by_name = self._by_name.get(normalized)
        if by_name is not None:
            return by_name
        return self._aliases.get(normalized)
