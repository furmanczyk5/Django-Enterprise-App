###################################
Local Development Environment Setup
###################################

The planning.org web portal is mostly written in `Django <https://docs.djangoproject.com>`_, with a smaller REST API that is written in `Node <https://nodejs.org>`_. At a minimum, you will need:

- `Python 3 <https://python.org>`_
- Node,
- `git <https://git-scm.com/>`_
- `bash <https://www.gnu.org/software/bash/>`_
- `RabbitMQ <https://www.rabbitmq.com/>`_

installed on your machine (see sections below for specific instructions and caveats to installing these) to contribute code and deploy it to our staging and production environments. There are also some `system libraries <https://pillow.readthedocs.io/en/5.1.x/installation.html#external-libraries>`_ ( ``libjpeg`` and ``zlib`` most importantly) needed by one of the Python requirements, the Pillow imaging library. These may or may not be already present on your operating system. See `this StackOverflow post <https://stackoverflow.com/a/34631976>`_ for guidance.

The ``pdfkit`` dependcy also requires the `wkhtmltopdf system library to be installed <https://github.com/JazzCore/python-pdfkit/wiki/Installing-wkhtmltopdf>`_

*******************************
Git, GitHub, and Source Control
*******************************

.. highlight:: bash

We use ``git`` for source control and the remote repository is hosted on `GitHub <https://github.com>`_. You will need to create an account on GitHub if you don't currently have one. Once you do, we will add your GitHub username to our `organization <https://github.com/apa-dev>`_ and you should be able to check out the repo. To use the command-line client, navigate to where you want the repo on your local filesystem (or append the full path one space after the command below), then type::

   $ git clone git@github.com:apa-dev/planning

There are also official `GUI clients <https://desktop.github.com/>`_ for OS X and Windows, if you prefer. If you're using Windows, you'll probably want the GUI client regardless, as it also ships with a ``bash`` shell that will be necessary for deploying to staging and prod.


**********************
Operating System Setup
**********************

We are using Python 3, specifically Python 3.5 although 3.6 should work as well. Python less than 3.5 and any version of Python 2 will not work.

Mac OS X
========

.. highlight:: bash

Mac OS X still ships with Python 2 by default for some reason, so you will need to install Python 3 yourself. The easiest method is to first install `Homebrew <https://brew.sh/>`_, a package manager for OS X. Follow the instructions on the Homebrew website to install it, then install Python 3 by typing::

   $ brew install python3

at a terminal. ``bash`` and the command-line version of ``git`` should already be present. You can install Node either by downloading and installing the binary from `the website <https://nodejs.org/en/>`_ or with Homebrew::

   $ brew install node

RabbitMQ can also be installed with homebrew::

   $ brew install rabbitmq

The binaries are placed in ``/usr/local/sbin``, which is not in your ``$PATH`` by default; you may want to add it there. Now you can start Rabbit::

   $ /usr/local/sbin/rabbitmq-server --detached

Linux
=====

Many flavors of Linux ship with Python 3 (and if it does not, installing it via your distribution's package manager is probably fairly straightforward). Some distributions may ship with both Python 2 and 3, and the default ``python`` binary might be Python 2, whereas the Python 3 binary might be ``python3``. Just be aware of this when creating the virtual environment - it's best to explicitly use ``python3`` when doing so. You may have to install those ``libjpeg`` and ``zlib`` libraries mentioned at the beginning of this document. The StackOverflow post has some guidance for Ubuntu and Fedora, but your distribution or version might be different, so you might have to do some experimenting.

``bash`` should obviously already be installed; ``git`` likely will be as well. If using Ubuntu or any Debian-based distribution, Node should be installed from the ``nodesource`` ``apt`` repo, as there may be a conflict with an existing binary called ``node`` present on those systems. Consult the `node documentation <https://nodejs.org/en/download/package-manager/>`_ for details.

RabbitMQ can likely be installed with your distribution's package manager, although the default repo may be out of date. Check the `RabbitMQ docs <https://www.rabbitmq.com/download.html>`_ for details on installing and where the ``rabbitmq-server`` binary will be located by default, so that you can start up Rabbit in the same method as outlined above in the OS X section.


************
Django Setup
************

Assuming you successfully cloned the repo, it's now time to create a Python virtual environment. Virtual environments are a handy way to keep your Python project dependencies separate from one another and your operating system. It also sets up your ``PYTHONPATH`` correctly. Creating a virtual environment will create a folder containing a copy of the version of Python you choose and then anything you install with ``pip install`` will be placed there. We recommend you choose a location outside of the project repo, otherwise you'll have to remember to add the virtual environment folder name to the ``.gitignore`` file to avoid accidentally committing a ton of unnecessary data to the repo. A popular choice is ``~/.envs``, as this keeps it hidden and is also the default used by some virtual environment helper tools, such as `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_::

   $ mkdir ~/.envs

Now create a Python 3 virtual environment::

   $ python3 -m venv ~/.envs/planning

On Mac OS X, if you want to be extra sure you're using the Homebrew-installed version, you can use the full path to the Homebrew Python binary (the <VERSION> depends on the version Homebrew installs; as of this writing it is ``3.6.5``)::

   $ /usr/local/Cellar/python/<VERSION>/bin/python3 -m venv ~/.envs/planning

Assuming this succeeded, you now need to "activate" the virtual environment::

   $ source ~/.envs/planning/bin/activate

by default most shells should now show ``(planning)`` preceding the ``$`` prompt to let you know you're in a virtual environment.  You can verify that your virtual environment is active by typing::

   (planning) $ which python

in the shell. If the response is ``~/.envs/planning/bin/python`` (or wherever you installed the virtual env), you're ready to install required packages with ``pip``, the Python package management tool. From the project root::

   (planning) $ pip install --upgrade pip  # may be necessary in some cases
   (planning) $ pip install -r requirements.txt

All of our project dependencies will be pulled down and installed. Watch the output for errors (the previously mentioned issues with Pillow and system libraries are a common source), but if everything succeeded, you can move on to Node Setup.

**********
Node Setup
**********

Parts of the REST API for the planning.org website are written in Node. This component is in the ``api_node`` directory under the project root. ``cd`` into that directory, then run::

   $ npm install

To install the required dependencies.

In addition, we use the `Django-Compressor <http://django-compressor.readthedocs.io/en/latest/>`_ library to bundle some static assets (mostly CSS files), and we specify `less <http://lesscss.org/>`_ as our CSS precompiler. This means the ``lessc`` binary needs to be accessible on your ``$PATH``, so you need to install ``less`` globally, with some important caveats.

less Global Install
===================

Depending on your operating system and method of Node/npm installation, you may need superuser privileges to install ``npm`` packages globally, as in ``sudo npm install -g less``. But this less than desireable, as you may need to use a different version than the one installed globally but your ``$PATH`` may default to one or the other. However, if you must install globally, it is highly recommended to at least configure ``npm`` to use a user-writeable location for global packages. Follow the `guide at the npm docs <https://docs.npmjs.com/getting-started/fixing-npm-permissions>`_ for instructions. Ensure that whatever location you choose is now in your ``$PATH``::

   $ echo $PATH
   $ # should see ~/.npm-global/bin (or wherever you chose)
   $ # somewhere in the output

now if ``$ npm install -g less`` runs successfully, ``$ which lessc`` should show the path to the location you chose.

**************
Database Setup
**************

We currently use two databases for planning.org: `PostgreSQL <https://postgresql.org>`_, which backs a lot of the data models on the site, and `iMIS <https://www.advsol.com/asi/IMIS20/solutions/association_management_software.aspx>`_, which contains a lot of our membership data.

Postgres setup
==============

.. highlight:: python

Although you could install Postgres locally, run migrations, and try to load in fixtures and mock data from there, it is much easier to simply point to a dev database we already have set up on the office network (which obviously means you'll need to VPN in if you're remote). This database is periodically synced with prod and it will be much easier to debug problems with "real-enough" data. Getting set up this way is as easy as properly configuring your settings, in ``planning/settings/local.py`` (copy ``planning/settings/local.template`` to ``local.py`` if you haven't already::

   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql_psycopg2',
           'NAME': 'apa',
           'USER': 'planning',
           'PASSWORD': '<ASK FOR PASSWORD>',
           'HOST': '192.241.175.29', # 192.241.167.12,
           'PORT': '5432',
       },
       'MSSQL': {
           'NAME': 'imis_live',
           'ENGINE': 'sql_server.pyodbc',
           'HOST': 'SQLDEV.apac.planning.org', #'HOST': '38.124.107.158',
           'USER': 'django',
           'PASSWORD': '<ASK FOR PASSSWORD>',
           'PORT':'1433',
           'OPTIONS': {
               'driver': 'FreeTDS',
               'host_is_server': True,
               'unicode_results': True,
               'extra_params': 'TDS_VERSION=7.4',
           },
           'TEST': {
               'NAME': 'imis_live',
               },
           'USE_LIVE_FOR_TESTS': True
           }
   }

.. highlight:: bash

Obviously, you will need to ask someone on the team for the actual passwords. You can verify that you're successfully able to connect to Postgres with client software. If you have Postgres installed locally, you can use its ``psql`` command-line client::

    $ psql -h 192.241.175.29 -U planning -d apa
    $ # enter password when prompted
    $ # should now see a prompt that looks like
    $ # apa=>

There are also several GUI tools, such as `pgAdmin <https://www.pgadmin.org/>`_, that you could use if you prefer.

iMIS Setup
==========

iMIS uses MS SQL Server as its database. To connect to it from UNIX-like environments, such as OS X and Linux, you will need to install the `FreeTDS libraries <http://www.freetds.org/>`_.

OS X Install and Configuration
------------------------------

::

   $ brew install freetds --with-unixodbc


.. highlight:: cfg

Then, create a file (or update if already exists) at ``/usr/local/etc/odbcinst.ini``, with the following values::

   [FreeTDS]
   Description = TD Driver (MSSQL)
   Driver = /usr/local/lib/libtdsodbc.so
   Setup = /usr/local/lib/libtdsodbc.so

Linux Install and Configuration
-------------------------------

Depends on your distribution, but the package to install probably contains ``freetds`` in it somewhere. The configuration file location and ``Driver`` and ``Setup`` values will likely be similar to the OS X file above, though possibly just ``/etc`` for the file path and ``/usr/lib`` instead of ``/usr/local/lib``.


Verifying Your Setup and Connecting to iMIS
-------------------------------------------

Although a ``freetds.conf`` file is not necessary for connecting to iMIS from our Django app, you will need one if connecting with other client tools (OS X location: ``/usr/local/etc/freetds.conf``). Append the following to that file::

   # Staging
   [MSSQL]
   host = SQLDEV
   port = 1433
   tds version = 7.4

See the `freetds documentation <http://www.freetds.org/userguide/freetdsconf.htm>`_ or ``man freetds.conf`` for more options.

.. highlight:: bash

Now (if you're on the office network or VPN-ed in) you can try connecting with the command-line ``tsql`` client (there are also some `fancy GUI clients <https://itunes.apple.com/us/app/sqlpro-studio/id985614903?mt=12>`_)::

   $ tsql -H SQLDEV -p 1433 -U django -D imis_live -P <PASSWORD>


.. highlight:: tsql

If didn't get any errors and can see a prompt that ends with something like ``1>``, you have successfully connected. Try viewing all the iMIS Table names::

   SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'
   go


Connecting Remotely via SSH Tunneling
-------------------------------------

With the new Azure-hosted SQL Server databases, the Cradlepoint VPN connection no longer works for connecting when outside of the office network. A workaround would be to use an SSH tunnel through staging.

.. highlight:: bash

First, open a terminal and establish a local port forwarding connection::

   $ ssh -L 14330:devsql01.planning.org:1433 -N username@192.241.188.216

This will forward traffic from port 14330 on your local machine to the dev iMIS SQL Server via staging (the ``-N`` tells it to not run a command on staging).

.. highlight:: python

Then, edit your local settings and change the ``MSSQL`` database connection object to use 14330 for the PORT and localhost for the HOST, e.g.::

   'DATABASES': {
        'MSSQL': {
            'PORT': '14330',
            'HOST': 'localhost',
            # all other parameters should stay the same
        }
   }

Now you should be able to connect to iMIS when remote. Test at a ``python manage.py shell``::

   >>> from imis.models import Name
   >>> Name.objects.last()  # should return the most recent Name record

.. highlight:: bash

You could also repeat this method for Solr. Open another terminal and::

   $ ssh -L 9983:162.243.16.153:8983 -N username@192.241.188.216

Then change the ``SOLR`` value in your local settings to ``http://localhost:9983``

*************************
Celery and RabbitMQ Setup
*************************

.. highlight:: bash

Assuming you successfully installed RabbitMQ as outlined in the `Operating System Setup`_ chapter, you can now create a user, password, and vhost. Note the following commands assume the filesystem location for rabbitmq binaries is in your ``$PATH`` ( ``/usr/local/sbin`` if installed with Homebrew on OS X).

Start RabbitMQ::

   $ rabbitmq-server --detached

Stop RabbitMQ::

   $ rabbitmqctl stop

Create user, password, and vhost. These are the default used by the ``BROKER_URL`` value in ``planning/settings/base.py``; feel free to create different values for these, but then be aware you'll have to add a ``BROKER_URL`` value to your ``plannig/settings/local.py`` to reflect those changes::

   $ rabbitmq-server --detached
   $ rabbitmqctl add_user myuser mypassword
   $ rabbitmqctl add_vhost myvhost
   $ rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"

Start a celery worker (virtual environment must be activated)::

   (planning) $ python manage.py celeryd --verbosity=2 --loglevel=DEBUG

Start Celerybeat (task scheduler; virtual environment must be activated)::

   (planning) $ python manage.py celerybeat --verbosity=2 --loglevel=DEBUG

Purge the queue (be **VERY CAREFUL** about doing this, it will permanently delete data)::

   (planning) $ celery -A planning.celery purge

.. warning::

   Unlike the Django dev server, Celery does not auto-detect code changes or restart itself. If you're working on something Celery-related, you will need to manually restart the worker to see the effects.


Celery Logging
==============

.. highlight:: python

Uncaught Exceptions will always be sent to `Sentry <https://sentry.io/american-planning-association/planning/>`_, but if you want to log additional information about a Celery task you can use the built-in ``logging`` library at the ``error`` level, e.g.::

   import logging

   from celery import shared_task
   from django_cereal.pickle import DJANGO_CEREAL_PICKLE

   logger = logging.getLogger(__name__)

   @shared_task(name="my_task", serializer=DJANGO_CEREAL_PICKLE)
   def task_to_log():
       try:
            # ... some code that could raise an Exception
       except Exception as exc:
           logger.error(exc.__str__())

***************
Django Settings
***************

In the project root, the ``planning`` folder has another folder called ``settings`` (i.e.: ``<repo_root>/planning/settings``). There are two important files in here, ``base.py`` and ``local.template``. As you might imagine, ``base.py`` contains settings that are independent of environment type (prod, staging, local), whereas ``local.template`` is specific to your environment and also contains sensitive settings like passwords and API keys that we don't want in the repo. Copy ``local.template`` to ``local.py`` (if you haven't already) and edit some important values accordingly.

SECRET_KEY
==========

.. highlight:: bash

Can be anything on local. If you want a realistic one and have ``pwgen`` installed::

   $ pwgen -sy -r \" 64 1

DATABASES
=========

See `Postgres setup`_ section above.

SOLR
====

`Solr is a full-text search server <http://lucene.apache.org/solr/features.html>`_. We have a dev instance set up for you to connect to.

.. highlight:: python

::

   SOLR = "http://162.243.16.153:8983"

RESTIFY_SERVER_ADDRESS
======================

`restify <http://restify.com/>`_ is the Node REST API we use, and it should be set to::

   RESTIFY_SERVER_ADDRESS = 'http://local-development.planning.org:8080'

AWS_S3_ACCESS_KEY_ID
====================

Ask someone on the dev team for this.

AWS_S3_SECRET_ACCESS_KEY
========================

Ask someone on the dev team for this.

SCHOLAR_LAB_ADDRESS
===================

::

   SCHOLAR_LAB_ADDRESS = "http://planning.scholarlab.com"

SCHOLAR_LAB_API_KEY
===================

Ask someone on the dev team for this.

SESSION_COOKIE_DOMAIN
=====================

We need to fake a FQDN with some features and services, first set its value here in your ``local.py`` settings::

   SESSION_COOKIE_DOMAIN = 'local-development.planning.org'

.. highlight:: sh

Then add it to your ``/etc/hosts`` file as well::

   127.0.0.1 local-development.planning.org

CADMIUMCD_API_KEY
=================

Ask someone on the dev team for this.

CADMIUMCD_REGISTRATION_TASK_ID
==============================

.. highlight:: python

::

   CADMIUMCD_REGISTRATION_TASK_ID = '52343'

PROMETRIC_FTP_PORT
==================

.. highlight:: python

::

   PROMETRIC_FTP_PORT = 990

PROMETRIC_FTP_USERNAME
======================

::

   PROMETRIC_FTP_USERNAME = 'AICP'

PROMETRIC_FTP_HOST
==================

::

   PROMETRIC_FTP_HOST = '63.95.218.81'

PROMETRIC_FTP_PASSWORD
======================

Ask someone on the dev team for this.

API_KEY
=======

Ask someone on the dev team for this.

LEARN_DOMAIN
============

::

   LEARN_DOMAIN = 'apa.staging.coursestage.com'


**********
Deployment
**********

.. highlight:: bash

First, you will need to copy ``planning/_deploy/local_settings_example.sh`` to ``planning/_deploy/local_settings.sh`` and edit accordingly::

   deploy_user="$USER"
   venv_path="${HOME}/.envs/planning"  # or wherever you installed it

Now you will need user accounts set up and your SSH keys copied over to our staging and production servers. You will need:

- your SSH public key (by default, ``~/.ssh/id_rsa.pub``)
- an existing team member to SSH in to the servers and create a user for you::

   $ USERNAME=<your chosen or assigned username>
   $ sudo useradd -m -G sudo,worker -s /bin/bash $USERNAME
   $ sudo passwd $USERNAME
   $ # choose a good password
   $ sudo mkdir /home/$USERNAME/.ssh
   $ sudo nano /home/$USERNAME/.ssh/authorized_keys
   $ # paste in contents of your SSH public key to this file, then save and quit
   $ sudo chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh

Now, you can try SSH-ing yourself from your machine::

   $ ssh $USERNAME@ip-address

If it works, press ``Ctrl-D`` to log out and copy over your private key so that when you deploy you will be able to check out your changes from the git repo::

   $ scp ~/.ssh/id_rsa $USERNAME@ip-address:/home/$USERNAME/.ssh/

Now test deploying ``master`` to ``staging``, by using the scripts in the ``_deploy`` folder of the repo::

   $ bash _deploy/staging_deploy.sh.command

This will deploy to staging, without installing any new requirements or running database migrations (as these changes are infrequent and take time). If you do need to install new requirements::

   $ bash _deploy/staging_deploy_full.sh.command

And/or run database migrations::

   $ bash _deploy/staging_deploy_full_migrate.sh.command

There are similarly-named scripts for deploying to production, with ``prod`` substituted for ``staging``

*******
Testing
*******

.. highlight:: python

In order to run automated tests, you will need to have several variables set in your local settings ``planning/settings/local.py``::

   # We define a custom test runner so that:
   # 1. Django doesn't try to create a separate database on our MS SQL iMIS server with pyodbc
   # 2. We can use live data for tests instead of loading in fixtures or sample data
   TEST_RUNNER = 'planning.test_runner.UseLiveDatabaseTestRunner'

   # in the DATABASES dictionary, make sure that MSSQL has 'USE_LIVE_FOR_TESTS' set to True
   DATABASES: {
       'default': '...'  # see Postgres Setup section for details
       },
       'MSSQL': {
           'NAME': 'imis_live',
           '...': '...'  # see Postgres Setup section for details

           # Make sure this is set for MSSQL!
           'USE_LIVE_FOR_TESTS': True
        }
    }

Secondly, we used to use a ``sqlite3`` database for testing. This appears to be no longer possible, as sqlite seems to not be able to support some of the more complex queries such as those with the :obj:`django.db.models.Q` operator. Current attempts at running tests with the ``local_db`` sqlite database in the repo yielded syntax errors deep in the Django ORM libraries. In any case, ideally your test environment should mirror that of production as closely as possible, so we shouldn't be testing with sqlite for that reason alone. So, check your local settings to make sure you're not using this sqlite database, check your settings for a line that starts with::

   if 'test' in sys.argv:
       DATABASES: {
           'NAME': 'local_db',
           # ...
       }

and comment it out or delete it.

.. highlight:: bash

You should now be able to run tests with::

   (planning) $ python manage.py test
   (planning) $ # optionally increase the verbosity to see what it's really doing
   (planning) $ python manage.py test --verbosity=2
   (planning) $ # preserve the db between runs, useful for running tests on quick changes
   (planning) $ # so that you don't have to wait for it to run all migrations on a fresh db
   (planning) $ python manage.py test --keepdb
   (planning) $ # test a single Django app
   (planning) $ python manage.py test store
