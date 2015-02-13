import logging
from allauth.account.signals import user_signed_up, email_confirmed
from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from model_utils import Choices
from django.db import models
from django.utils.translation import ugettext_lazy as _
import recurrence.fields

__author__ = 'guglielmo'

class Rule(models.Model):
    STATUS = Choices(
        (0, 'compliant', _('Compliant')),
        (1, 'noncompliant', _('Non compliant')),
        (2, 'error', _('Error generating')),
        (3, 'unverified', _('Unverified'))
    )

    title = models.CharField(_("title"), default="", max_length=128, help_text=_("A rule's title"))
    tags = models.CharField(_("tags"), default="",
                            max_length=128, blank=True, help_text=_("One or more tags, used to form groups"))
    slug = AutoSlugField(populate_from='title', always_update=True)
    description = models.TextField(_("description"), blank=True, null=True, help_text=_("An extensive description of the rule"))
    is_active = models.BooleanField(_('is active'), help_text=_("Whether the rule is active or closed"), default=True)
    created_at = models.DateTimeField(_("creation date"), help_text=_("The date and time when the rule was created"), blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(_("modification date"), help_text=_("The date and time when the rule was last modified"), blank=True, null=True, auto_now=True)
    author = models.CharField(_("author"), max_length=128, help_text=_("The rule's author"), blank=True, null=True)
    launch_recurrences = recurrence.fields.RecurrenceField(_("launch recurrences"), blank=True, null=True)
    task = models.CharField(_("task"), max_length=128, help_text=_("The management task name. Must be paired to an actual task, created by a programmer."), blank=True, null=True)
    default_parameters = models.CharField(max_length=128, help_text=_("Default parameters, as a key/value csv sequence: k1=v1,k2=v2,k3=v3,..."), blank=True, null=True)

    def __unicode__(self):
        return u"{0}".format(self.title)

    @property
    def status(self):
        last_launched = self.last_launched()
        if last_launched:
            return self.STATUS[last_launched.outcome].translate(settings.LANGUAGE_CODE)
        return self.STATUS[3].translate(settings.LANGUAGE_CODE)

    @property
    def last_launched_at(self):
        last_launched = self.last_launched()
        if last_launched:
            return last_launched.launch_ts
        return None

    @property
    def notes(self):
        last_launched = self.last_launched()
        if last_launched:
            return last_launched.note
        return None


    def last_launched(self):
        return self.verification_set.order_by('-launch_ts').first()

    class Meta:
        verbose_name = _("Rule")
        verbose_name_plural = _("Rules")


class Verification(models.Model):
    OUTCOME = Choices(
        (0, 'succeded', _('Succeded')),
        (1, 'failed', _('Failed')),
        (2, 'error', _('Generated an error')),
    )
    rule = models.ForeignKey(Rule)
    launch_ts = models.DateTimeField(_("launch timestamp"), help_text=_("The date and time when the verification was launched"))
    duration = models.IntegerField(_("duration"), blank=True, null=True, help_text=_("Duration of the verification, in seconds"))
    outcome = models.IntegerField(_('verification'), choices=OUTCOME, null=True, blank=True, help_text=_("Verification outcome"))
    csv_report = models.FileField(blank=True, null=True, help_text=_("CSV report generated"), upload_to="reports/%Y/%m/%d")
    user = models.ForeignKey(User, help_text=_("The operator that launched the verification"))
    parameters = models.CharField(max_length=128, help_text=_("Parameters, as a key/value csv sequence: k1=v1,k2=v2,k3=v3,..."), blank=True, null=True)
    note = models.CharField(max_length=1024, blank=True, null=True, help_text=_("A note, to describe particular issues emerged in the verification, max 256 chars."))


    def csv_report_link(self):
        if self.csv_report:
            return mark_safe("<a href='%s'>download report</a>" % (self.csv_report.url,))
        else:
            return "No report"

    def __unicode__(self):
        return u"{0}".format(self.launch_ts)

    class Meta:
        verbose_name = _("Verification")
        verbose_name_plural = _("Verifications")


@receiver(user_signed_up)
def add_is_staff(sender, **kwargs):
    """
    add is_staff, is_superuser and operator group to users that sign up

    since the only method to sign up is by the external depp.accesso account,
    this is done every time a user signs up through the depp.accesso account.

    :param sender: The class sending the signal
    :param kwargs: KW arguments sent along with the signal
    :return: void
    """
    social_login = kwargs['sociallogin'].account
    user = kwargs['user']

    try:

        extra_data = social_login.extra_data

        # staff users and superusers should retain their status
        if 'is_superuser' in extra_data:
            user.is_superuser = extra_data['is_superuser']
        if 'is_staff' in extra_data:
            user.is_staff = extra_data['is_staff']
            # staff users should be added to operator group
            og = Group.objects.get(name__iexact='operator')
            user.groups.add(og)

        user.save()

    except ObjectDoesNotExist as e:
        pass


