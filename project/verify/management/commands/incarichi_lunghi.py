# -*- coding: utf-8 -*-
from datetime import datetime
from optparse import make_option
from dateutil.relativedelta import relativedelta
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q

__author__ = 'guglielmo'

class Command(VerifyBaseCommand):
    """
    Verify that an institution charge is shorter than 5 years
    List the exceptions
    """
    help = "Check that all institution charges have a duration of less than 5 years."

    option_list = VerifyBaseCommand.option_list + (
        make_option('--institution_id',
            dest='institution_id',
            default=0,
            help='Institution IDs (1,2=C/P EU, 3=Gov, 4,5=Parl/Sen, 6,7=G/C Reg, 8,9=G/C Prov, 10,11=G/C Com, 12=Comm, 14=AssSind )',
        ),
    )


    def execute_verification(self, *args, **options):
        institution_id = int(options['institution_id'])
        self.csv_headers = [
            "NOME", "COGNOME", "OP_ID", "DATA NASCITA", "LUOGO NASCITA",
            "PARTITO", "INCARICO", "ISTITUZIONE",
            "LOCALITA", "PROV", "DATA INIZIO INCARICO"
        ]

        if institution_id:
            self.logger.info(
                "Verification {0} launched with institution_id set to {1}".format(
                    self.__class__.__module__, institution_id
                )
            )
        else:
            self.logger.info(
                "Verification {0} launched for all institutions".format(
                    self.__class__.__module__
                )
            )

        # verification process
        self.ok_locs = []

        five_yrs_ago = datetime.now() - relativedelta(years=5)

        qs = OpInstitutionCharge.objects.using('politici').filter(
            date_end__isnull=True, content__deleted_at__isnull=True
        ).filter(
            date_start__lt=five_yrs_ago.strftime('%Y-%m-%d')
        )

        if institution_id:
            qs = qs.filter(
                institution__id=institution_id
            )

        qs = qs.exclude(
            Q(institution__id=12) |
            Q(charge_type__name__iexact='senatore a vita')
        )
        qs = qs.select_related().values_list(
            'politician__first_name', 'politician__last_name', 'politician__content_id',
            'politician__birth_date', 'politician__birth_location',
            'party__name', 'charge_type__name',
            'institution__name', 'location__name', 'location__prov', 'date_start'
        )

        self.ko_locs = qs.order_by(
            'institution__id', 'location__location_type', '-location__inhabitants'
        )



        if len(self.ko_locs):
            outcome = Verification.OUTCOME.failed
            self.logger.info(
                "  failure! {0} non-compliant charges found.".format(
                    len(self.ko_locs)
                )
            )
        else:
            outcome = Verification.OUTCOME.succeded
            self.logger.info(
                "  success! all charges are compliant."
            )

        return outcome


