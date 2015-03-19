# -*- coding: utf-8 -*-
from datetime import datetime
from itertools import groupby, tee, islice, izip_longest, ifilter
from optparse import make_option
from dateutil.relativedelta import relativedelta
from utils import get_next
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q

__author__ = 'guglielmo'

class Command(VerifyBaseCommand):
    """
    Verify that an institution charge has no overlapping charge
    List the exceptions
    """
    help = "Check that all institution charges are not overlapping," +\
            "or discontinuous over time."

    option_list = VerifyBaseCommand.option_list + (
        make_option('--type',
            dest='type',
            help='dicover overlappings or doscontinuities',
        ),
        make_option('--max-days',
            dest='max_days',
            default=30,
            help="Number of days to declare a discontinuity")
    )


    def execute_verification(self, *args, **options):
        self.csv_headers = [
            "INCARICO", "ISTITUZIONE",
            "LOCALITA", "PROV", "DATA_INIZIO", "DATA_FINE",
        ]

        self.logger.info(
            "Verification {0} launched for all institutions".format(
                self.__class__.__module__
            )
        )

        max_days = int(options['max_days'])
        verification_type = options['type']
        if verification_type not in ('overlap', 'discontinuity'):
            raise Exception("Wrong parameter type passed to task. Possible values: ovelap, discontinuity.")

        # verification process
        self.ok_locs = []

        qs = OpInstitutionCharge.objects.using('politici').filter(
            content__deleted_at__isnull=True
        )

        qs = qs.filter(
            Q(charge_type__name__iexact='sindaco') |
            Q(charge_type__name__iexact='presidente') & Q(institution__name__iexact='giunta provinciale') |
            Q(charge_type__name__iexact='presidente') & Q(institution__name__iexact='giunta regionale') |
            Q(charge_type__name__iexact='presidente del consiglio') & Q(institution__name__iexact='governo nazionale') |
            Q(charge_type__name__iexact='commissario') & Q(institution__name__iexact='commissione europea') |
            Q(charge_type__name__iexact='presidente della repubblica')
        )
        qs = qs.select_related().values_list(
            'charge_type__name', 'institution__name',
            'location__name', 'location__prov', 'date_start', 'date_end'
        )

        data = qs.order_by(
            'institution__id', 'location__location_type', '-location__inhabitants'
        )

        # groups all charges by the first 4 fields:
        # charge name, institution name, location name, prov
        for key, group in groupby(data, lambda x: x[0:4]):
            # generate sorted list, using 5th field (date_start) as sorting key
            g = sorted(list(group), key=lambda x: x[4])

            # extract all elements whose date_end (6th field)
            # is greater than the start_date (5th field) of the successive element
            if verification_type == 'overlap':
                exceptions = ifilter(
                    lambda x: x[1] and x[0][5] and x[1][4] and
                              (x[0][5] > x[1][4]), get_next(g)
                )
            else:
                exceptions = ifilter(
                    lambda x: x[1] and x[0][5] and x[1][4] and
                              ((g[1][4] - g[0][5]).days > max_days), get_next(g)
                )

            for e in exceptions:
                self.ko_locs.append(e[0])
                self.ko_locs.append(e[1])

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


