# -*- coding: utf-8 -*-
from optparse import make_option
from django.utils import timezone
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q

__author__ = 'guglielmo'

class Command(VerifyBaseCommand):
    """
    Verify that all cities don't have a Vicesindaco Facente Funzione
    (extracts all those cities having it)
    """
    args = '<op_location_id op_location_id ...>'
    help = "Check that all locations don't have a Vicesindaco Facente Funzione"

    option_list = VerifyBaseCommand.option_list + (
        make_option('--ab-threshold',
                    dest='ab_threshold',
                    default=0,
                    help='Limit extractions to cities having more than ab_threshold inhabitants'),
        )


    def execute_verification(self, *args, **options):
        ab_threshold = int(options['ab_threshold'])
        self.csv_headers = ["NOME", "LOC ID", "ABITANTI"]

        launch_ts = timezone.now()
        self.logger.info(
            "Verification {0} launched with threshold set to {1}".format(
                self.__class__.__module__, ab_threshold
            )
        )

        # verification process
        # todo: substitute IDs with names or strings
        self.ko_locs_ids = OpInstitutionCharge.objects.using('politici').filter(
            date_end__isnull=True, content__deleted_at__isnull=True
        ).filter(location__inhabitants__gt=ab_threshold).filter(
            charge_type__id=22
        ).values_list('location__id', flat=True)

        self.ko_locs = OpLocation.objects.using('politici').filter(
            inhabitants__gt=ab_threshold,
            location_type__id=6, date_end__isnull=True
        ).filter(id__in=self.ko_locs_ids).order_by('-inhabitants').values_list('name', 'id', 'inhabitants')

        if len(self.ko_locs):
            outcome = Verification.OUTCOME.failed
            self.logger.info(
                "  failure! {0} non-compliant locations found.".format(
                    len(self.ko_locs)
                )
            )
        else:
            outcome = Verification.OUTCOME.succeded
            self.logger.info(
                "  success! all locations are compliant."
            )

        return outcome