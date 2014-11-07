Openpolis verification tasks
============================

Management tasks and admin interface for verifying openpolis data consistency"

See `project/` folde for the source code (django/python).

See `docs/` for a still uncomplete documentation.

Development
-----------

Clone this repository, get in the created folder, then run:
::

    $ pip install -r requirements/development.txt
    $ python project/manage.py runserver

Testing
-------

To start all Django TestCase modules:

::

    $ python project/manage.py test

To start functional test with selenium:

::

    $ python project/manage.py test tests.functional_tests

License
-------

See LICENSE.txt file
See authors of this project in CONTRIBUTORS.txt


-----

Generated with `cookiecutter`_ and `openpolis`_ /`django16-template`_ 0.1


.. _cookiecutter: https://github.com/audreyr/cookiecutter
.. _openpolis: https://github.com/openpolis
.. _django16-template: https://github.com/openpolis/django16-template
