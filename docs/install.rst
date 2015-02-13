Install
=========

This is where you write how to get a new laptop to run this project,
so that you can start developing.

Prerequisites
-------------
Python 2.7, pip, virtualenv and virtualenvwrapper, as global packages.

A read-only connection to the ``politici`` mysql database, or a replica of it.,

Steps
-----
.. code::

    mkdir op-verify
    cd op-verify
    mkvirtualenv op-verify
    setvirtualenvproject
    git clone git@github.com:openpolis/op-verify.git
    pip install -r requirements/development.txt
    cp config/samples/.env config/.env
    # edit config/.env file, as needed (DEBUG, and DATABASE_URL)


Notes
-----




