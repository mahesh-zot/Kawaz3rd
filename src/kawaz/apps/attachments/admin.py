from django.contrib import admin
from .models import Material

class MaterialAdmin(admin.ModelAdmin):
    readonly_fields = ('slug', 'author', 'ip_address', 'created_at',)
    search_fields = ('author__username', 'author__nickname')
admin.site.register(Material, MaterialAdmin)
