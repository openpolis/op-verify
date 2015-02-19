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

        self.csv_headers = ["ISTITUZIONE", "INCARICO", "N_DONNE", "N_UOMINI", "N_TOTALI", "PERC_DONNE", "PERC_UOMINI"]

        institutions = OpInstitution.objects.using('politici').all()
        if args:
            institutions = institutions.filter(id__in=args)
            self.logger.info(
                "Verification {0} launched with institutions limited to {1}".format(
                    self.__class__.__module__, ",".join(institutions.values_list('id', flat=True))
                )
            )
        else:
            self.logger.info(
                "Verification {0} launched for all institutions".format(
                    self.__class__.__module__
                )
            )

        self.ok_locs = []
        self.ko_locs = []

        for institution in institutions:

            charge_types_ids = OpInstitutionCharge.objects.using('politici').\
                filter(date_end__isnull=True,
                       content__deleted_at__isnull=True).\
                filter(institution=institution).\
                values_list('charge_type', flat=True).\
                distinct()
            charge_types = OpChargeType.objects.using('politici').\
                filter(id__in=charge_types_ids)

            for charge_type in charge_types:
                self.logger.info(
                    "Counting {0} in {1}".format(
                        charge_type.name, institution.name
                    )
                )
                qs = OpInstitutionCharge.objects.using('politici').\
                    filter(date_end__isnull=True,
                           content__deleted_at__isnull=True).\
                    filter(institution=institution,
                           charge_type=charge_type)

                n_tot = qs.count()
                n_fem = qs.filter(politician__sex__iexact='f').count()
                n_mal = n_tot - n_fem

                merged = [institution.name, charge_type.name, n_fem, n_mal, n_tot,]
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


