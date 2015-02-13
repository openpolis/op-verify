from django.contrib import admin
from django.core.management import call_command, CommandError
from django.http import StreamingHttpResponse
from .models import Rule, Verification

__author__ = 'guglielmo'

def run_verification(request, id):
    response = StreamingHttpResponse(stream_generator(request, id), content_type="text/html")
    return response

def stream_generator(request, id):
    rule = Rule.objects.get(pk=id)

    yield "Verifying rule: %s ... <br/>" % rule  # Returns a chunk of the response to the browser
    yield " " * 1000
    try:
        call_command(rule.task, rule_id=rule.pk, verbosity='2', username=request.user.username)
        yield " Rule verification terminated. Status: {0}<br/>".format(rule.status)
        yield ' Go back to <a href="/admin/verify/rule/{0}">rule page</a>.<br/>'.format(rule.id)
        yield " " * 1000

    except CommandError as e:
        yield " ! %s<br/>" % e
        yield " " * 1000
    except Exception as e:
        yield " ! Error in execution: %s<br/>" % e
        yield " " * 1000


class VerificationInline(admin.TabularInline):
    model = Verification
    extra = 0
    exclude = ('csv_report', )
    list_display = readonly_fields = ('launch_ts', 'duration', 'outcome', 'user', 'csv_report_link', 'parameters')

    def get_queryset(self, request):
        return super(VerificationInline, self).get_queryset(request).order_by('-launch_ts')

class RuleAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'status', 'last_launched_at', 'notes']
    inlines = [VerificationInline,]
    search_fields = ['title']

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
