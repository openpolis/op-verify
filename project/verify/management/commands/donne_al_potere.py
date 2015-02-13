# -*- coding: utf-8 -*-
from collections import OrderedDict
import locale
from optparse import make_option
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q, Count

__author__ = 'guglielmo'

class Command(VerifyBaseCommand):
    """
    Verify that all locations have a non-null component of male members
    """
    args = '<institution_id institution_id ...>'
    help = "Check that all locations have only male components (list locations with female components)."

    option_list = VerifyBaseCommand.option_list + (
        make_option('--institution_id',
            dest='institution_id',
            default=6, # giunta regionale
            help='Institution IDs (6=Giunta Reg, 8=Giunta Prov, 10=Giunta Com)',
        ),
    )


    def execute_verification(self, *args, **options):
        institution_id = int(options['institution_id'])
        self.csv_headers = ["LOCALITA", "PROV", "ABITANTI", "N_DONNE", "N_TOTALI", "PERC"]

        self.logger.info(
            "Verification {0} launched with institution_id set to {1}".format(
                self.__class__.__module__, institution_id
            )
        )

        # verification process
        self.ok_locs = []


        qs = OpInstitutionCharge.objects.using('politici').filter(
            date_end__isnull=True, content__deleted_at__isnull=True
        ).filter(
            institution__id=institution_id
        )

        if institution_id in (10, 11):          # giunta o consiglio comunale
            qs = qs.filter(
                location__name__in=self.get_capoluoghi()
            )
        elif institution_id in (6, 7, 8, 9):    # giunte o consigli provinciali o regionali
            pass
        else:
            raise Exception("Wrong parameters passed to task.")

        total = qs.values_list(
                'location__name', 'location__prov', 'location__inhabitants'
        ).annotate(
            num=Count('location')
        ).order_by(
            '-location__inhabitants'
        )
        total = OrderedDict([(item[0], (item[1], item[2], item[3])) for item in total])

        fem = qs.values_list(
                'location__name', 'location__prov', 'location__inhabitants'
        ).filter(
            politician__sex__iexact='f'       # sesso femminile
        ).annotate(
            num=Count('location')
        ).order_by(
            '-location__inhabitants'
        )
        fem = OrderedDict([(item[0], (item[1], item[2], item[3])) for item in fem])

        # add number of women / total
        l = []
        for k, v in total.items():
            merged = [k, v[0], v[1]]
            n_fem = fem[k][2] if k in fem else 0
            merged.append("{0}".format(n_fem))
            merged.append("{0}".format(total[k][2]))
            merged.append(locale.format("%.2f",100. * n_fem / float(total[k][2]) ))
            l.append(merged)

        self.ko_locs = l
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


