Notes for developers
====================

Multiple databases
------------------

The application connects to two databases:
 - the application database, containing rules, verification outcomes, users, ...
 - the politici database, containing all the daa to be verified

 Connection to the politici database is read-only.

Politici DB as replica
----------------------
The politici database accessed by the application is a replica slave of the production database.

Verification tasks
------------------

Verification tasks are management tasks extending the
``verify.management.commands.VerifyBaseCommand`` class.

``VerifyBaseCommand`` extends ``django.core.management.base.BaseCommand``
and contains the logic common to all verification tasks:

- parse general options and arguments,
- launch the real verification code,
- analyze the outcome,
- add the related verification record to the db,
- write the CSV to the file system, in case issues are detected

To add a new verification task, the class must extend ``VerifyBaseCommand``,
and override the ``execute_verification`` method.

``execute_verification`` must return an outcome, chosen from ``Verification.OUTCOME``
values (succeeded, failed, error).


Adding a new Rule
-----------------

To add a new Rule, one must access the admin interface, create a new Rule instance,
and connect that to an existing verification task.

The connection is done by writing the name of the task in the ``Task`` field.

The name of the task is the name of the python file in which the task is
implemented, under ``project/verify/management/commands/``.

A Rule can be passed options, in the ``Default Parameters`` field.
The options can be read in the ``execute_verification`` method, through the ``options`` dictionary.

So, for example, if a new Rule is created, having::

    title: "Cities with no president",
    task: "no_president",
    default_parameters: "location_type_id=4"

Then the task implemented in the no_president.py file will be launched, when
the **Run verificatio** button is pressed , and it will have a ``location_type_id``
in the ``options`` dictionary.


- Streaming results


Capoluoghi
----------

There are 8200 *comuni* or cities in Italy, and 110 *province*.
The 110 cities that are capitals of their provinces, are called Capoluoghi.

The complete list of capoluoghi is here:
http://it.wiktionary.org/wiki/Appendice:Elenco_Capoluoghi_di_Provincia

It can be parsed into a CSV file, by using the DataMiner Chrome extension.
The resulting file is under the project folder, and it's converted into json with
this command::

    csvcut -c1,2,3  project/capoluoghi.csv | csvjson --indent=4 > capoluoghi.json

The second volumn header has been renamed "Provincia", and contains the name of the
Province, only when this is different from the name of the city.

This is used in the verification tasks, to extract only the capoluoghi cities::

import json
import os
from django.conf import settings
capoluoghi_json_filename = os.path.join(settings.PROJECT_PATH, 'capoluoghi.json')
json_file=open(capoluoghi_json_filename)
data = json.load(json_file)
capoluoghi =  [d['Capoluogo'] for d in data]


Todo
----

- Improve feedback for showing output of verification tasks to user.
- Automatic recurring launches (celery?)
- Notifications (mail, integration with Slack)
