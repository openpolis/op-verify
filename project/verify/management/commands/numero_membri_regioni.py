# -*- coding: utf-8 -*-
from collections import OrderedDict
from optparse import make_option
import os
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q, Count
import json

__author__ = 'guglielmo'

N_MEMBRI = {
    'consiglio': {
        'Valle D\'Aosta': 35,
        'Piemonte': 50,
        'Lombardia': 80,
        'Trentino Alto Adige': 70,
        'Veneto': 50,
        'Friuli Venezia Giulia': 49,
        'Liguria': 30,
        'Emilia Romagna': 50,
        'Toscana': 40,
        'Umbria': 20,
        'Marche': 30,
        'Lazio': 50,
        'Abruzzo': 30,
        'Molise': 20,
        'Campania': 50,
        'Puglia': 50,
        'Basilicata': 20,
        'Calabria': 30,
        'Sicilia': 90,
        'Sardegna': 60,
    },
    'giunta': {
        'Valle D\'Aosta': 4,
        'Piemonte': 10,
        'Lombardia': 16,
        'Trentino Alto Adige': 14,
        'Veneto': 10,
        'Friuli Venezia Giulia': 10,
        'Liguria': 6,
        'Emilia Romagna': 10,
        'Toscana': 8,
        'Umbria': 4,
        'Marche': 5,
        'Lazio': 10,
        'Abruzzo': 6,
        'Molise': 4,
        'Campania': 10,
        'Puglia': 10,
        'Basilicata': 4,
        'Calabria': 6,
        'Sicilia': 18,
        'Sardegna': 12,
    },
}


class Command(VerifyBaseCommand):
    """
    Verify that all regions have the correct number of members
    """
    args = '<op_location_id op_location_id ...>'
    help = "Check that all comuni have the correct number of members"

    option_list = VerifyBaseCommand.option_list + (
        make_option('--institution',
            dest='institution',
            default='consiglio',
            help='Institutions (giunta|consiglio)',
        ),
    )


    def execute_verification(self, *args, **options):
        institution = options['institution']
        self.csv_headers = ["NOME", "LOC ID", "N CONSIGLIERI", "N PREVISTO", "ABITANTI"]

        self.logger.info(
            "Verification {0} launched with institution set to {1}".format(
                self.__class__.__module__, institution
            )
        )

        if institution == 'giunta':
            institution_id = 6
            charge_type_id = 12
        else: # consiglio
            institution_id = 7
            charge_type_id = 13

        locs = OpLocation.objects.using('politici').filter(
            opinstitutioncharge__institution__id=institution_id,
            opinstitutioncharge__charge_type__id=charge_type_id,
            opinstitutioncharge__date_end__isnull=True,
            opinstitutioncharge__content__deleted_at__isnull=True,
        ).order_by('-inhabitants').annotate(
            n=Count('opinstitutioncharge')
        )

        for l in locs:
            # skip regions with commissari
            try:
                has_commissario = l.opinstitutioncharge_set.get(
                    charge_type__id=16, # commissario
                    date_end__isnull=True
                )
                continue
            except ObjectDoesNotExist:
                pass

            self.logger.debug(u'Processing location {0}'.format(l.name))

            n_consiglieri = N_MEMBRI[institution][l.name]
            if institution == 'consiglio':
                if l.n != N_MEMBRI[institution][l.name]:
                    self.ko_locs.append((l.name, l.id, l.n, n_consiglieri, l.inhabitants))
            else:
                if l.n > N_MEMBRI[institution][l.name]:
                    self.ko_locs.append((l.name, l.id, l.n, n_consiglieri, l.inhabitants))


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