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
    Verify that all cities with a Commissario, don't have other active charges
    (extracts all those cities having it)
    """
    args = '<op_location_id op_location_id ...>'
    help = "Check that all locations with a Commissario, don't have other active charges"

    option_list = VerifyBaseCommand.option_list + (
        make_option('--ab-threshold',
                    dest='ab_threshold',
                    default=0,
                    help='Limit extractions to cities having more than ab_threshold inhabitants'),
        )


    def execute_verification(self, *args, **options):
        ab_threshold = int(options['ab_threshold'])
        self.csv_headers = ["NOME", "LOC ID", "ABITANTI", "N. INCARICHI"]

        launch_ts = timezone.now()
        self.logger.info(
            "Verification {0} launched with threshold set to {1}".format(
                self.__class__.__module__, ab_threshold
            )
        )

        # verification process
        self.comms_locs_ids = OpInstitutionCharge.objects.using('politici').filter(
            date_end__isnull=True, content__deleted_at__isnull=True
        ).filter(
            location__location_type__id=6
        ).filter(
            charge_type_id=16
        ).order_by('-location__inhabitants').values_list('location', flat=True).distinct()

        self.ko_locs = []
        for lid in self.comms_locs_ids:
            l = OpLocation.objects.using('politici').get(id=lid)
            self.logger.debug(u" checking {0}".format(l.name))
            n_incarichi = l.opinstitutioncharge_set.filter(
                    date_end__isnull=True, content__deleted_at__isnull=True
            ).exclude(charge_type_id=16).count()
            if (n_incarichi > 0):
                self.ko_locs.append([l.name, l.id, l.inhabitants, n_incarichi])

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