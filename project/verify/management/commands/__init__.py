# -*- coding: utf-8 -*-

from optparse import make_option
import logging
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

__author__ = 'guglielmo'

class VerifyBaseCommand(BaseCommand):
    """
    Base command class for verification tasks
    """
    args = ''
    help = "--- Define help in extending commands"

    option_list = BaseCommand.option_list + (
        make_option('--limit',
                    dest='limit',
                    default=0,
                    help='Limit of records to import'),
        make_option('--offset',
                    dest='offset',
                    default=0,
                    help='Offset of records to start from'),
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: no actual import is made'),
        make_option('--overwrite',
                    dest='overwrite',
                    default=False,
                    action='store_true',
                    help='Always overwrite values in the new DB from values in the old one'),
        make_option('--parameters',
                    dest='parameters',
                    default='',
                    help='Parameters, when passed through the admin interface'),
        make_option('--username',
                    dest='username',
                    default='admin',
                    help='Logged user launching the command'),
        )

    logger = logging.getLogger('management')

    def pre_handle(self, *args, **options):

        self.verbosity = options['verbosity']

        # inject parameters into class, as attributes
        # if passed through the 'parameters' option
        # happens when calling command from admin
        self.parameters = options['parameters']
        if self.parameters:
            params_dict = dict(
                tuple(p.split("=")) for p in self.parameters.split(",")
            )
            for k,v in params_dict.items():
                self.__setattr__(k, v)


        if self.verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif self.verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif self.verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif self.verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        self.username = options['username']
        self.dryrun = options['dryrun']
        self.overwrite = options['overwrite']

        self.offset = int(options['offset'])
        self.limit = int(options['limit'])
