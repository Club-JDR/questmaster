"""Static catalog of grantable admin permissions (RBAC capability registry).

Permissions form a fixed catalog defined in code (stable keys the enforcement
decorators reference), while the *grants* (who holds what) live in the database.
This keeps route decorators referencing compile-time constants rather than
DB-resolved strings.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    """A grantable capability.

    Attributes:
        key: Stable identifier referenced by ``require_permission`` decorators.
        label: French label shown in the admin permissions UI.
        section: Admin endpoint this capability unlocks (for nav filtering).
    """

    key: str
    label: str
    section: str


PERMISSIONS: list[Permission] = [
    Permission("users.view", "Consulter les utilisateurs", "admin.list_users"),
    Permission("vtt.manage", "Gérer les VTTs", "admin.list_vtts"),
    Permission("system.manage", "Gérer les systèmes", "admin.list_systems"),
    Permission("trophy.manage", "Gérer les badges", "admin.list_trophies"),
    Permission("channel.manage", "Gérer les catégories de salons", "admin.list_channels"),
    Permission("special_event.manage", "Gérer les événements", "admin.list_special_events"),
    Permission("game_event.view", "Consulter les journaux", "admin.list_game_events"),
    Permission("discord.send", "Envoyer des messages Discord", "admin.list_discord_messages"),
    Permission("permissions.manage", "Gérer les permissions", "admin.list_permissions"),
]

PERMISSION_KEYS: frozenset[str] = frozenset(p.key for p in PERMISSIONS)
