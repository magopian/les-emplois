from django.contrib import admin

from ..utils.admin import ItouModelAdmin
from . import models, views


class SettingAdmin(ItouModelAdmin):
    """Admin View for settings"""

    def has_add_permission(self, request):
        return False  # Hide the admin "+ Add" link for Queues

    def has_change_permission(self, request):
        return False

    def has_module_permission(self, request):
        """
        return True if the given request has any permission in the given
        app label.
        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to view the module on
        the admin index page and access the module's index page. Overriding it
        does not restrict access to the add, change or delete views. Use
        `ModelAdmin.has_(add|change|delete)_permission` for that.
        """
        return request.user.is_superuser

    def changelist_view(self, request):
        """The 'change list' admin view for this model."""
        # proxy request to setting view
        return views.settings_list(request)


admin.site.register(models.Setting, SettingAdmin)
