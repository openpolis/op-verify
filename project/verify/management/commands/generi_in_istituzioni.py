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
    Report delle statistiche di genere complessive, a livello nazionale,
    per tutti gli organi di tutte le istituzioni.
    Può limitarsi a una o più istituzioni, se si passa un elenco di institution_id
    """
    args = '<institution_id institution_id ...>'
    help = "Check that all locations have only male components (list locations with female components)."

    option_list = VerifyBaseCommand.option_list

    def execute_verification(self, *args, **options):

        self.csv_headers = ["ISTITUZIONE", "N_DONNE", "N_UOMINI", "N_TOTALI", "PERC_DONNE", "PERC_UOMINI"]

        all_institutions_ids = OpInstitution.objects.using('politici').values_list('id', flat=True)
        if args:
            institution_ids = list( set(map(str, all_institutions_ids)) & set(args) )
            self.logger.info(
                "Verification {0} launched with institutions limited to {1}".format(
                    self.__class__.__module__, ",".join(institution_ids)
                )
            )
        else:
            self.logger.info(
                "Verification {0} launched for all institutions".format(
                    self.__class__.__module__
                )
            )


        qs = OpInstitutionCharge.objects.using('politici').filter(
            date_end__isnull=True, content__deleted_at__isnull=True
        )
        if args:
            qs = qs.filter(institution__in=institution_ids)

        mal_qs = qs.filter(politician__sex__iexact='m')
        fem_qs = qs.filter(politician__sex__iexact='f')

        total = OrderedDict(qs.values_list('institution__name').\
            annotate(num=Count('institution')).\
            order_by('institution__id'))

        fem = OrderedDict(fem_qs.values_list('institution__name').\
            annotate(num=Count('institution')).\
            order_by('institution__id'))

        mal = OrderedDict(mal_qs.values_list('institution__name').\
            annotate(num=Count('institution')).\
            order_by('institution__id'))

        self.ok_locs = []
        self.ko_locs = []
        for k, n_tot in total.items():
            n_mal = 0
            n_fem = 0
            if k in mal:
                n_mal = mal[k]
            if k in fem:
                n_fem = fem[k]
            merged = [k, n_fem, n_mal, n_tot,]
            merged.append(locale.format("%.2f",100. * n_fem / float(n_tot) ))
            merged.append(locale.format("%.2f",100. * n_mal / float(n_tot) ))
            self.ko_locs.append(merged)

        outcome = Verification.OUTCOME.failed
        self.logger.info(
            "Report for {0} institutions generated.".format(
                len(self.ko_locs)
            )
        )
        return outcome


