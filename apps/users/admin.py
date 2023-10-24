from django.contrib import admin

from .models import CustomUser, Follow, UserPoints


admin.site.register(CustomUser)
admin.site.register(Follow)
admin.site.register(UserPoints)
