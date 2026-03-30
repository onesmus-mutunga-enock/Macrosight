from rest_framework.permissions import BasePermission


class CostsPermission(BasePermission):
    """
    Base permission class for costs module operations.
    """
        return user.role.code in ['SUPER_ADMIN', 'ECONOMIC_ANALYST'] if hasattr(user, 'role') else False
