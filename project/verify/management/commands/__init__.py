# -*- coding: utf-8 -*-
import csv
import json

from optparse import make_option
import os
import csvkit
from django.core.files import File
from django.core.management.base import BaseCommand
from os.path import normpath, join
from django.utils import timezone
from verify.models import *

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
        make_option('--username',
                    dest='username',
                    default='admin',
                    help='Logged user launching the command'),
        make_option('--rule-id',
                    dest='rule_id',
                    default=0,
                    help='Id of the rule to associate the task'),
        )

    logger = logging.getLogger('management')


    def execute_verification(self, *args, **options):
        raise Exception("Not implemented")

    def handle(self, *args, **options):

        self.verbosity = options['verbosity']
        self.username = options['username']
        self.dryrun = options['dryrun']
        self.overwrite = options['overwrite']

        self.offset = int(options['offset'])
        self.limit = int(options['limit'])

        # set log level, from verbosity
        if self.verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif self.verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif self.verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif self.verbosity == '3':
            self.logger.setLevel(logging.DEBUG)


        # if rule_id is passed as an argument
        # parameters taken from the rule override defaults
        r = None
        self.rule_id = int(options['rule_id'])
        if self.rule_id:
            r = Rule.objects.get(pk=self.rule_id)
            if r.default_parameters:
                params_dict = dict(
                    tuple(p.split("=")) for p in r.default_parameters.split(",")
                )
                for k,v in params_dict.items():
                    options[k] = v

        launch_ts = timezone.now()

        self.note = None
        self.ok_locs = []
        self.ko_locs = []
        self.csv_headers = []

        module_name = self.__class__.__module__
        task_name = module_name.split(".")[-1]

        try:
            # verification process
            outcome = self.execute_verification(*args, **options)
        except Exception as e:
            outcome = Verification.OUTCOME.error
            self.note = unicode(e)
            self.logger.warning(unicode(e))


        # Verification added to Rule
        v = None
        if r:
            v = r.verification_set.create(
                launch_ts=launch_ts,
                outcome=outcome,
                duration=(timezone.now() -launch_ts).seconds,
                user=User.objects.get(username=self.username),
                parameters=r.default_parameters,
                note=self.note
            )

        if outcome == Verification.OUTCOME.failed:
            # report creation (csv)
            if self.rule_id:
                csvname = "{0}_{1}.csv".format(r.slug, launch_ts.strftime("%H%M%S"))
            else:
                csvname = "{0}_{1}.csv".format(task_name, launch_ts.strftime("%H%M%S"))
            csv_filename = normpath(join(settings.MEDIA_ROOT, csvname))

            if v:
                self.logger.debug("  {0} tmp file created".format(csv_filename))
            else:
                self.logger.info("  {0} report file created".format(csv_filename))

            with open(csv_filename, 'wb+') as destination:
                csvwriter = csvkit.CSVKitWriter(
                    destination, quoting=csv.QUOTE_NONNUMERIC
                )
                csvwriter.writerow(self.csv_headers)
                for i, loc in enumerate(self.ko_locs):
                    csvwriter.writerow(loc)
                    if i and i%100 == 0:
                        self.logger.debug("  {0} locations added to CSV".format(i))

                self.logger.debug("  all {0} locations added to CSV".format(len(self.ko_locs)))

                csv_report = File(destination)
                if v is not None:
                    v.csv_report = csv_report
                    v.save()
                    self.logger.debug("  {0} csv file added to Verification instance".format(v.csv_report.url))
                    os.remove(csv_filename)
                    self.logger.debug("  {0} tmp file removed".format(csv_filename))

        self.logger.info(
            "Verification {0} terminated after {1} seconds".format(
                module_name, timezone.now() - launch_ts
            )
        )

    def get_capoluoghi(self):
        """Returns the list of capoluoghi, as a
        list of city names"""

        capoluoghi_json_filename = os.path.join(settings.PROJECT_PATH, 'capoluoghi.json')
        json_file=open(capoluoghi_json_filename)
        data = json.load(json_file)
        return [d['Capoluogo'] for d in data]
