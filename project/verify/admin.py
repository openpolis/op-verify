from StringIO import StringIO
from django.contrib import admin
from django.core import serializers
from django.core.management import call_command, CommandError
from django.http import HttpResponse, StreamingHttpResponse
import time
from .models import Rule, Verification

__author__ = 'guglielmo'

def run_verification(request, id):
    return HttpResponse(stream_generator(id), content_type="text/plain")

def stream_generator(id):
    rule = Rule.objects.get(pk=id)

    yield "Verifying rule: %s" % rule  # Returns a chunk of the response to the browser
    try:
        call_command(rule.task, verbosity=2)
    except CommandError as e:
        yield " ! %s" % e
    except Exception as e:
        yield " ! Error in execution: %s" % e
    yield "\n"
    yield " " * 1000

class VerificationInline(admin.TabularInline):
    model = Verification
    extra = 0
    readonly_fields = ('launch_ts', 'duration', 'outcome', 'csv_report', 'user', 'parameters')

class RuleAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'status', 'last_launched_at', 'notes']
    inlines = [VerificationInline,]

    buttons = [
        {
         'url': 'run_verification',
         'textname': 'Run verification',
         'func': run_verification,
        },
    ]

    def change_view(self, request, object_id, form_url='', extra_context={}):
        extra_context['buttons'] = self.buttons
        return super(RuleAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        from django.conf.urls import patterns, url, include
        urls = super(RuleAdmin, self).get_urls()
        my_urls = list( (url(r'^(.+)/%(url)s/$' % b, self.admin_site.admin_view(b['func'])) for b in self.buttons) )
        return my_urls + urls

admin.site.register(Rule, RuleAdmin)
