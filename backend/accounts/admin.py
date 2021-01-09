from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

from .models import User


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('userid', 'username', 'email', 'is_active', 'is_superuser', 'date_joined')
    list_filter = ('is_superuser', 'is_active',)
    fieldsets = (
        (None, {'fields': ('userid', 'password')}),
        (_('Personal info'), {'fields': ('username', 'email', )}),
        (_('Permissions'), {'fields': ('is_active', 'is_superuser',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('userid', 'password1', 'password2')}
         ),
    )
    search_fields = ('userid', 'email')
    ordering = ('userid',)
    filter_horizontal = ()


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
