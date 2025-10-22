# src/models/base.py
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Type, TypeVar
from website.extensions import db

T = TypeVar("T", bound="SerializableMixin")


class SerializableMixin:
    """Mixin pour ajouter la sérialisation aux modèles."""

    # Champs à exclure de la sérialisation par défaut
    _exclude_fields = []

    # Champs de relation à ne pas sérialiser automatiquement
    _relationship_fields = []

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Sérialise le modèle en dictionnaire."""
        data = {}

        for column in self.__table__.columns:
            if column.name in self._exclude_fields:
                continue

            value = getattr(self, column.name)

            # Conversion des types spéciaux
            if isinstance(value, datetime):
                data[column.name] = value.isoformat()
            elif isinstance(value, Decimal):
                data[column.name] = float(value)
            else:
                data[column.name] = value

        if include_relationships:
            for rel_name in self._relationship_fields:
                rel_value = getattr(self, rel_name, None)
                if rel_value is None:
                    data[rel_name] = None
                elif isinstance(rel_value, list):
                    data[rel_name] = [
                        item.to_dict() if hasattr(item, "to_dict") else str(item)
                        for item in rel_value
                    ]
                else:
                    data[rel_name] = (
                        rel_value.to_dict()
                        if hasattr(rel_value, "to_dict")
                        else str(rel_value)
                    )

        return data

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Crée une instance depuis un dictionnaire."""
        # À implémenter dans chaque modèle
        raise NotImplementedError

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Met à jour l'instance depuis un dictionnaire."""
        protected_fields = {"id", "created_at", "updated_at"}

        for key, value in data.items():
            if key in protected_fields or key in self._relationship_fields:
                continue
            if hasattr(self, key):
                setattr(self, key, value)
