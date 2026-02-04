from datetime import datetime
from decimal import Decimal
from typing import Any, Self
from website.extensions import db


class SerializableMixin:
    """Mixin to add serialization capabilities to models."""

    _exclude_fields = []
    _relationship_fields = []

    def _serialize_value(self, value):
        """Convert a column value to a JSON-compatible type."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

    def _serialize_relationship(self, rel_value):
        """Serialize a single relationship value (None, list, or object)."""
        if rel_value is None:
            return None
        if isinstance(rel_value, list):
            return [
                item.to_dict() if hasattr(item, "to_dict") else str(item)
                for item in rel_value
            ]
        return rel_value.to_dict() if hasattr(rel_value, "to_dict") else str(rel_value)

    def to_dict(self, include_relationships: bool = False) -> dict[str, Any]:
        """Serialize the model to a dictionary."""
        data = {}
        for column in self.__table__.columns:
            if column.name not in self._exclude_fields:
                data[column.name] = self._serialize_value(getattr(self, column.name))

        if include_relationships:
            for rel_name in self._relationship_fields:
                data[rel_name] = self._serialize_relationship(
                    getattr(self, rel_name, None)
                )

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create an instance from a dictionary. Must be implemented by subclasses."""
        raise NotImplementedError

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update the instance from a dictionary."""
        protected_fields = {"id", "created_at", "updated_at"}

        for key, value in data.items():
            if key in protected_fields or key in self._relationship_fields:
                continue
            if hasattr(self, key):
                setattr(self, key, value)
