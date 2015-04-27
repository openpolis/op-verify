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
    Verify that all Mayors have a defined electoral coalition or party
    """
    args = '<op_location_id op_location_id ...>'
    help = "Check that all Mayors have a defined electoral coalition or party"

    option_list = VerifyBaseCommand.option_list + (
        make_option('--ab-threshold',
                    dest='ab_threshold',
                    default=0,
                    help='Limit extractions to cities having more than ab_threshold inhabitants'),
        )


    def execute_verification(self, *args, **options):
        ab_threshold = int(options['ab_threshold'])
        self.csv_headers = [
            "NOME", "COGNOME", "OP_ID", "DATA NASCITA", "LUOGO NASCITA",
            "LOCALITA", "PROV", "DATA INIZIO INCARICO"
        ]

        launch_ts = timezone.now()
        self.logger.info(
            "Verification {0} launched with threshold set to {1}".format(
                self.__class__.__module__, ab_threshold
            )
        )

        # verification process
        self.ko_locs = []
        qs = OpInstitutionCharge.objects.using('politici').filter(
            date_end__isnull=True, content__deleted_at__isnull=True
        ).filter(location__inhabitants__gt=ab_threshold).filter(
            Q(institution__id=10) &
            Q(charge_type__id=14) | Q(charge_type__id=22)
        )

        qs = qs.filter(
            party__isnull=True
        )

        qs = qs.values_list(
            'politician__first_name', 'politician__last_name', 'politician__content_id',
            'politician__birth_date', 'politician__birth_location',
            'location__name', 'location__prov', 'date_start'
        )

        self.ko_locs = qs.order_by(
            '-location__inhabitants'
        )

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