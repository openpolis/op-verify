# -*- coding: utf-8 -*-
import csv
from optparse import make_option
import csvkit
from django.core.files import File
from django.utils import timezone
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q
from os.path import abspath, basename, dirname, join, normpath

__author__ = 'guglielmo'


class Command(VerifyBaseCommand):
    """
    Verify that all cities have a Sindaco or a Commissario

    """
    args = '<op_location_id op_location_id ...>'
    help = "Check that all locations have a Sindaco or a Commissario"

    option_list = VerifyBaseCommand.option_list + (
        make_option('--ab-threshold',
                    dest='ab_threshold',
                    default=0,
                    help='Limit extractions to cities having more than ab_threshold inhabitants'),
        )

    def handle(self, *args, **options):

        # prepare the handle command
        self.pre_handle(*args, **options)

        if 'ab_threshold' in self.__dict__:
            ab_threshold = int(self.__getattribute__('ab_threshold'))
        else:
            ab_threshold = int(options['ab_threshold'])
            self.parameters = "ab_threshold={0}".format(ab_threshold)

        launch_ts = timezone.now()
        self.logger.info(
            "Verification {0} launched with threshold set to {1}".format(
                self.__class__.__module__, ab_threshold
            )
        )

        module_name = self.__class__.__module__
        task_name = module_name.split(".")[-1]

        note = None
        csv_report = None

        # verification process
        # todo: substitute IDs with names or strings
        try:
            ok_locs = OpInstitutionCharge.objects.using('politici').filter(
                date_end__isnull=True, content__deleted_at__isnull=True
            ).filter(location__inhabitants__gt=ab_threshold).filter(
                Q(charge_type__id=16) | (
                    Q(institution__id=10) &
                    Q(charge_type__id=14) | Q(charge_type__id=22)
                )
            ).values_list('location__id', flat=True)

            ko_locs = OpLocation.objects.using('politici').filter(
                inhabitants__gt=ab_threshold,
                location_type__id=6, date_end__isnull=True
            ).exclude(id__in=ok_locs).order_by('-inhabitants').values_list('name', 'id', 'inhabitants')

            if ko_locs.count():
                outcome = Verification.OUTCOME.failed
            else:
                outcome = Verification.OUTCOME.succeded
        except Exception as e:
            outcome = Verification.OUTCOME.error
            note = unicode(e)

        # Verification added to Rule
        r = Rule.objects.get(task=task_name)
        v = r.verification_set.create(
            launch_ts=launch_ts,
            outcome=outcome,
            duration=(timezone.now() -launch_ts).seconds,
            user=User.objects.get(username=self.username),
            parameters=self.parameters,
            csv_report=csv_report,
            note=note
        )

        if outcome == Verification.OUTCOME.failed:
            # report creation (csv)
            csvname = "{0}_{1}.csv".format(task_name, launch_ts.strftime("%H%M%S"))
            csv_filename = normpath(join(settings.MEDIA_ROOT, 'reports', csvname))

            with open(csv_filename, 'wb+') as destination:
                csv_report = File(destination)
                csvwriter = csvkit.CSVKitWriter(
                    csv_report
                )
                csvwriter.writerow(["NOME", "LOC ID", "ABITANTI"])
                for loc in ko_locs:
                    csvwriter.writerow(loc)
                v.csv_report = csv_report
                v.save()

        self.logger.info(
            "Verification {0} terminated".format(
                module_name
            )
        )
