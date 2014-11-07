from django.contrib import admin
from .models import Rule, Verification

__author__ = 'guglielmo'


class VerificationInline(admin.TabularInline):
    model = Verification
    extra = 0

    exclude = ('note',)

class RuleAdmin(admin.ModelAdmin):
    inlines = [VerificationInline,]


admin.site.register(Rule, RuleAdmin)
