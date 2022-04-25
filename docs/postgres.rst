####################
Postgres
####################

************
Environments
************

Postgres servers are hosted in Digital Ocean.

=====================================     ==================
Host Name                                 IP Address
=====================================     ==================
Dev
``db01do.planning.org-dev``               ``192.241.175.29``
Staging
``db01do.planning.org-stage``             ``162.243.4.129``
``db02do.planning.org-stage``             ``162.243.24.238``
Prod
``db01do.planning.org-live``              ``162.243.9.138``
``db02do.planning.org-live``              ``162.243.12.101``
=====================================     ==================

********************
Postgres Restore
********************

Currently you need to transfer backups to your Mac since we haven't added ssh keys for production to the staging and development postgres servers. We should upload the backups directly to the server when the keys have been added.

Transfer the desired database from postgres prod to your Mac::

   $ scp -C plowe@162.243.9.138:/srv/backups/database/planning_<current>.sql planning_backup.sql


Transfer database from your Mac to the desired Postgres server tmp directory. The IP below is for staging postgres. ::

   $ scp -C planning_backup.sql plowe@162.243.4.129:/tmp



SSH into the postgres database server::

    $ ssh plowe@162.243.4.129

Open Postgres::

    $ sudo -u postgres psql

Kill active users connected to the database. Make sure to replace the smart quotes with text quotes.::

   postgres=# SELECT pg_terminate_backend(pg_stat_activity.pid)
   FROM pg_stat_activity
   WHERE pg_stat_activity.datname = 'apa' AND pid <> pg_backend_pid();

Quit Postgres::

    postgres=# \q

Drop the APA database::

    $ sudo -u postgres dropdb apa

Create the APA database::

    $ sudo -u postgres createdb apa

Restore the backup to the newly created apa database::

    # sudo -u postgres psql apa < planning_backup.sql


