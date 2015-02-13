# -*- coding: utf-8 -*-
from optparse import make_option
from verify.management.commands import VerifyBaseCommand
from verify.models import *
from verify.politici_models import *
from django.db.models import Q

__author__ = 'guglielmo'

class Command(VerifyBaseCommand):
    """
    Verify that all locations have a male leader
    To list the locations with female leaders, actually
    """
    args = '<institution_id institution_id ...>'
    help = "Check that all locations have a male leader (list locations with female leaders)."

    option_list = VerifyBaseCommand.option_list + (
        make_option('--institution_id',
            dest='institution_id',
            default=6, # giunta regionale
            help='Institution IDs (6=Giunta Reg, 8=Giunta Prov, 10=Giunta Com)',
        ),
    )


    def execute_verification(self, *args, **options):
        institution_id = int(options['institution_id'])
        self.csv_headers = ["LOCALITA", "PROV", "ABITANTI", "NOME", "COGNOME", "PARTITO", "INCARICO"]

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
        ).filter(
            politician__sex__iexact='f'       # sesso femminile
        )

        if institution_id == 10:              # giunta comunale
            qs = qs.filter(
                location__name__in=self.get_capoluoghi()
            ).filter(
                Q(charge_type__id=16) |       # commissario
                Q(charge_type__id=14) |       # sindaco
                Q(charge_type__id=22)         # vice sindaco facente funzione
            ).values_list(
                'location__name', 'location__prov', 'location__inhabitants',
                'politician__first_name', 'politician__last_name',
                'party__name', 'charge_type__name'
            )
        elif institution_id in (6, 8):        # giunte provinciali o regionali
            self.csv_headers = ["LOCALITA", "ABITANTI", "NOME", "COGNOME", "PARTITO"]
            qs = qs.filter(
                charge_type__id=1             # presidente
            ).values_list(
                'location__name', 'location__inhabitants',
                'politician__first_name', 'politician__last_name',
                'party__name'
            )
        else:
            raise Exception("Wrong parameters passed to task.")


        self.ko_locs = qs.order_by('-location__inhabitants')



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


