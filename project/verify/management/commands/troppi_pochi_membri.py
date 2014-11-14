# -*- coding: utf-8 -*-
from optparse import make_option
import os
import csvkit
from django.core.files import File
from django.utils import timezone
import math
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q, Count
from os.path import abspath, basename, dirname, join, normpath

__author__ = 'guglielmo'


LIMITI_CONSIGLIERI = {
    'regione': {
        'Valle D\'Aosta': 35,
        'Piemonte': 51,
        'Lombardia': 80,
        'Trentino Alto Adige': 70,
        'Veneto': 60,
        'Friuli Venezia Giulia': 49,
        'Liguria': 40,
        'Emilia Romagna': 50,
        'Toscana': 55,
        'Umbria': 31,
        'Marche': 43,
        'Lazio': 51,
        'Abruzzo': 31,
        'Molise': 21,
        'Campania': 61,
        'Puglia': 70,
        'Basilicata': 21,
        'Calabria': 50,
        'Sicilia': 90,
        'Sardegna': 60,
    },
    # le soglie per il numero di consiglieri comunali variano in base
    # al numero di abitanti e dipendono dall'anno delle ultime elezioni
    'comune_pre_2011': {
        1000000: 60,
        500000: 50,
        250000: 46,
        100000: 40,
        30000: 30,
        10000: 20,
        5000: 16,
        3000: 16,
        0: 12
    },
    'comune_2011': {
        1000000: 48,
        500000: 40,
        250000: 36,
        100000: 32,
        30000: 24,
        10000: 16,
        5000: 12,
        3000: 12,
        0: 9
    },
    'comune_2012': {
        1000000: 48,
        500000: 40,
        250000: 36,
        100000: 32,
        30000: 24,
        10000: 16,
        5000: 10,
        3000: 7,
        0: 6
    },
    'comune_2014': {
        1000000: 48,
        500000: 40,
        250000: 36,
        100000: 32,
        30000: 24,
        10000: 16,
        5000: 12,
        3000: 12,
        0: 10
    }
}




class Command(VerifyBaseCommand):
    """
    Verify that all institutions have the correct number of members
    """
    args = '<op_location_id op_location_id ...>'
    help = "Check that all institutions have the correct number of members"

    option_list = VerifyBaseCommand.option_list + (
        make_option('--institution',
            dest='institution',
            default=0,
            help='Institution names (Consiglio Regionale, Giunta Regionale, ...) or IDs (5, 6, 7, 8, 9, 10, ...)',
        ),
        make_option('--ab-threshold',
            dest='ab_threshold',
            default=0,
            help='Limit extractions to cities having more than ab_threshold inhabitants'
        ),
    )


    def execute_verification(self, *args, **options):
        ab_threshold = int(options['ab_threshold'])
        institution_id = int(options['institution_id'])
        self.csv_headers = ["NOME", "LOC ID", "N CONSIGLIERI", "N PREVISTO", "ABITANTI"]

        self.logger.info(
            "Verification {0} launched with threshold set to {1}, institution_id set to {2}".format(
                self.__class__.__module__, ab_threshold, institution_id
            )
        )

        charge_type_id = 0
        if institution_id in (6, 10):
            charge_type_id = 12 # assessore
        elif institution_id in (7, 11):
            charge_type_id = 13 # consigliere
        else:
            raise Exception("Wrong institution_id")

        nmembers_dict = OpLocation.objects.using('politici').filter(
            opinstitutioncharge__institution__id=institution_id,
            opinstitutioncharge__charge_type__id=charge_type_id,
            opinstitutioncharge__date_end__isnull=True,
            opinstitutioncharge__content__deleted_at__isnull=True
        ).order_by('-inhabitants').annotate(
            n=Count('opinstitutioncharge')
        ).values_list('name', 'id', 'n', 'inhabitants')

        for l in nmembers_dict:
            # determina l'anno di elezione del sindaco corrente
            data_elezione = l.opinstitutioncharge_set.get(
                charge_type__id=14, # sindaco
                date_end__isnull=True
            ).date_start.strftime('%Y-%m-%d')

            anno_elezione = ''
            if data_elezione < '2011-01-01':
                anno_elezione = 'pre_2011'
            elif data_elezione < '2012-01-01':
                anno_elezione = '2011'
            elif data_elezione < '2014-01-01':
                anno_elezione = '2012'
            else:
                anno_elezione = '2014'

            # consiglio regionale
            if institution_id == 7:
                if l[2] != LIMITI_CONSIGLIERI['regione'][l[0]]:
                    self.ko_locs.append((l[0], l[1], l[2], LIMITI_CONSIGLIERI['regione'][l[0]], l[3]))
                else:
                    self.ok_locs.append(l)

            # consiglio comunale
            # Come normato dall'articolo 37, comma 1, del Decreto legislativo 18 agosto 2000, n. 267
            # e dalla legge 23 dicembre 2009, n. 191, modificata ed integrata dal D.L. 25 gennaio 2010, n. 2;
            # si aggiunga la legge 14 settembre 2011, n. 148.
            # Nelle regioni a statuto speciale (ad eccezione del Trentino-Alto Adige)
            # non ha avuto luogo nessuna riduzione: vedasi ad esempio la legge regionale
            # sarda n°10 del 2011, in particolare al comma 5 dell'articolo 2.
            if institution_id == 11:
                if l[2] != LIMITI_CONSIGLIERI['comune_{0}'.format(anno_elezione)][l[0]]:
                    self.ko_locs.append((l[0], l[1], l[2], LIMITI_CONSIGLIERI['regione'][l[0]], l[3]))
                else:
                    self.ok_locs.append(l)


            # giunta regionale
            # L'art. 14, comma 1, lett. b) del decreto-legge n. 138/2011 prevede che
            # il numero massimo degli assessori regionali sia pari o inferiore a un quinto
            # del numero dei consiglieri regionali, con arrotondamento all'unità superiore.
            if institution_id == 6:
                n_max_assessori = math.ceil(int(LIMITI_CONSIGLIERI['regione'][l[0]]) / 5)
                if l[2] > n_max_assessori:
                    self.ko_locs.append((l[0], l[1], l[2], n_max_assessori, l[3]))
                else:
                    self.ok_locs.append(l)

            # giunta comunale
            # La giunta è un organo collegiale composto dal sindaco, che ne è anche presidente,
            # e da un numero di assessori, stabilito dallo statuto comunale,
            # che nelle regioni a statuto ordinario non deve essere superiore a un quarto
            # arrotondato in eccesso, del numero dei consiglieri comunali,
            # computando a tale fine anche il sindaco, e comunque non superiore a dodici.
            if institution_id == 10:
                n_max_assessori = math.ceil(int(LIMITI_CONSIGLIERI['comune_{0}'.format(anno_elezione)][l[0]]) / 4)
                if l[2] > n_max_assessori:
                    self.ko_locs.append((l[0], l[1], l[2], n_max_assessori, l[3]))
                else:
                    self.ok_locs.append(l)


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