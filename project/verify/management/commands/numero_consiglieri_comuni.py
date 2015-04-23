# -*- coding: utf-8 -*-
from collections import OrderedDict
from optparse import make_option
import os
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q, Count
import json
from os.path import abspath, basename, dirname, join, normpath

__author__ = 'guglielmo'

N_MEMBRI = {
    'st_ordinario': OrderedDict([
        (1000000, 48),
        ( 500000, 40),
        ( 250000, 36),
        ( 100000, 32),
        (  30000, 24),
    ]),
    'st_ordinario_cl': OrderedDict([
        (1000000, 48),
        ( 500000, 40),
        ( 250000, 36),
        ( 100000, 32),
        (  30000, 32),
    ]),
    'sardegna': OrderedDict([
        (100000, 34),
        ( 30000, 28),
    ]),
    'sicilia': OrderedDict([
        (1000000, 54),
        ( 500000, 50),
        ( 250000, 46),
        ( 100000, 40),
        (  30000, 30),
    ]),
    'giunta': OrderedDict([
        (1000000, 12),
        ( 500000, 10),
        ( 250000, 9),
        ( 100000, 8),
        (  30000, 6),
    ]),
    'giunta_cl': OrderedDict([
        (1000000, 12),
        ( 500000, 10),
        ( 250000, 9),
        ( 100000, 8),
        (  30000, 8),
    ])
}


class Command(VerifyBaseCommand):
    """
    Verify that all comuni have the correct number of members
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
            institution_id = 10
            charge_type_id = 12
        else: # consiglio
            institution_id = 11
            charge_type_id = 13

        locs = OpLocation.objects.using('politici').filter(
            opinstitutioncharge__institution__id=institution_id,
            opinstitutioncharge__charge_type__id=charge_type_id,
            opinstitutioncharge__date_end__isnull=True,
            opinstitutioncharge__content__deleted_at__isnull=True,
            inhabitants__gte=30000
        ).order_by('-inhabitants').annotate(
            n=Count('opinstitutioncharge')
        )

        capoluoghi_file = os.path.join(settings.PROJECT_PATH, 'capoluoghi.json')
        with open(capoluoghi_file, 'r') as f:
            capoluoghi = [c['Capoluogo'] for c in json.load(f, encoding='utf8')]

        for l in locs:
            # skip comuni with commissari
            try:
                has_commissario = l.opinstitutioncharge_set.get(
                    charge_type__id=16, # commissario
                    date_end__isnull=True
                )
                continue
            except ObjectDoesNotExist:
                pass

            self.logger.debug(u'Processing location {0}'.format(l.name))

            # consiglio comunale
            limiti = {}
            if institution == 'consiglio':
                if l.regional_id in (6, 8): # trentino
                    n_membri = 40
                else:
                    if l.regional_id == 22: # sardegna
                        limiti = N_MEMBRI['sardegna']
                    elif l.regional_id == 21: # sicilia
                        limiti = N_MEMBRI['sicilia']
                    else:
                        if l.name in capoluoghi:
                            limiti = N_MEMBRI['st_ordinario_cl']
                        else:
                            limiti = N_MEMBRI['st_ordinario']

            else: # giunta comunale
                if l.name in capoluoghi:
                    limiti = N_MEMBRI['giunta']
                else:
                    limiti = N_MEMBRI['giunta_cl']

            for lim, nc in limiti.items():
                if l.inhabitants > lim:
                    n_consiglieri = nc
                    break

            if l.n != n_consiglieri:
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