# -*- coding: utf-8 -*-
from optparse import make_option
from django.utils import timezone
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *

__author__ = 'guglielmo'

class Command(VerifyBaseCommand):
    """
    Verify that all cities have a Presidente for the Consiglio
    """
    args = '<op_location_id op_location_id ...>'
    help = "Check that all locations have a Presidente for the Consiglio"

    option_list = VerifyBaseCommand.option_list + (
        make_option('--location-type-id',
            dest='location_type_id',
            default=6,
            help='Location type IDs (4=R, 5=P, 6=C)',
        ),
        make_option('--ab-threshold',
            dest='ab_threshold',
            default=0,
            help='Limit extractions to cities having more than ab_threshold inhabitants'
        ),
    )


    def execute_verification(self, *args, **options):
        ab_threshold = int(options['ab_threshold'])
        location_type_id = int(options['location_type_id'])
        self.csv_headers = ["NOME", "LOC ID", "ABITANTI"]

        launch_ts = timezone.now()
        self.logger.info(
            "Verification {0} launched with threshold set to {1}, location_type_id set to {2}".format(
                self.__class__.__module__, ab_threshold, location_type_id
            )
        )

        # verification process
        self.ok_locs = OpInstitutionCharge.objects.using('politici').filter(
            date_end__isnull=True, content__deleted_at__isnull=True
        ).filter(
            location__location_type_id=location_type_id,
            location__inhabitants__gt=ab_threshold
        ).filter(
            charge_type__id=1,
            institution__id__in=(7, 9, 11)
        ).values_list('location__id', flat=True)

        self.ko_locs = OpLocation.objects.using('politici').filter(
            inhabitants__gt=ab_threshold,
            location_type__id=location_type_id, date_end__isnull=True
        ).exclude(id__in=self.ok_locs).order_by('-inhabitants').values_list('name', 'id', 'inhabitants')

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