####################
Server Configuration
####################

************
Environments
************

We provision our cloud infrastructure on `Digital Ocean <https://digitalocean.com>`_. Credentials for logging in to the DO account are stored in `Clipperz <https://clipperz.is>`_, our password management solution. We have three environments, dev, staging, and prod. Dev is obviously meant for development. The database is periodically synced with staging in order to provide realistic data when developing and avoiding the hassle of setting up Postgres and Solr locally and loading in data (at the expense of slower network connections).


===================================     ==================
DO name                                 IP Address
===================================     ==================
Dev
``db01do.planning.org-dev``             ``192.241.175.29``
Staging
``db01do.planning.org-stage``           ``162.243.4.129``
``db02do.planning.org-stage``           ``162.243.24.238``
``solr01do.planning.org-stage-dev``     ``162.243.16.153``
``web01do.planning.org-stage``          ``192.241.188.216``
Prod
``db01do.planning.org-live``            ``159.203.116.129``
``db02do.planning.org-live``            ``64.225.0.204``
``solr01do.planning.org-live``          ``162.243.9.52``
``web01do.planning.org-live``           ``192.241.179.148``
``web02do.planning.org-live``           ``192.241.185.8``
===================================     ==================

***********
Web Servers
***********

NGINX
=====

`NGINX <https://www.nginx.com/>`_ is the web server used. It functions as a reverse proxy to the `uWSGI`_ instance serving up the Django app itself as well as static files, specified in ``/srv/sites/apa/etc/nginx/locations.conf`` (this file is also stored in the repo in ``_deploy/nginx/local``. The nginx root config (i.e., the contents of ``/etc/nginx``) is stored in the repo in ``_deploy/nginx/server``, with the config file specific to our site is in ``_deploy/nginx/server/sites-available/default``.

uWSGI
=====

The Django app itself is served up with `uWSGI <https://uwsgi-docs.readthedocs.io/en/latest/>`_. The configuration file in the repo is located in ``_deploy/uwsgi.ini``, and `Supervisor`_ currently expects it to be in ``/srv/sites/apa/etc/uwsgi.ini`` on the server.


***************************************
Server Process Configuration Management
***************************************

Supervisor
==========

The various processes needed for planning.org are started/stopped/restarted with `Supervisor <http://supervisord.org>`_. Configuration files for the various processes and Supervisor itself are located in the project repo, in ``_deploy/supervisor``


******************************
Locations and Commands to Know
******************************

web1 and web2
=============

====================================== ======================================================================================
Location                               Description
====================================== ======================================================================================
``/srv/sites/apa``                     Main project folder
``/srv/sites/apa/proj/apa``            Django project
``/srv/sites/apa/htdocs``              Static/media files and assets
``/srv/sites/apa/envs``                Python virtual environments used by project
``/srv/sites/apa/log``                 Log directory for project
``/etc/supervisor/conf.d``             supervisor configurations for Django, Node, Celery
``/etc/nginx/nginx.conf``              Nginx main config
``/etc/nginx/sites-available/default`` Nginx config for Django site
``/srv/backups/logs``                  backup logs
``/srv/backups/duplicity``             filesystem backups configs/logs (backups are in AWS-S3 bucket : ``00_system_backups``)
====================================== ======================================================================================

.. highlight:: bash

Activate project virtual environment::

   $ venv apa

Restart django/uwsgi server::

   $ sudo supervisorctl restart django

Restart celery workers::

   $ sudo supervisorctl restart celery

Restart node::

   $ sudo supervisorctl restart node

Collect static assets::

   $ cd /srv/sites/apa/proj/apa
   $ venv apa
   $ ./manage.py collectstatic

Run migrations::

   $ cd /srv/sites/apa/proj/apa
   $ venv apa
   $ ./manage.py migrate

Remount GlusterFS::

   $ sudo mount -t glusterfs planning-web01do:/volume1 /srv/sites/apa/htdocs/media/

db1 and db2
===========

============================ ==============================
Location                     Description
============================ ==============================
``/etc/postgresql/9.5/main`` postgresql configs
``/srv/backups/database``    db backup dumps
``/srv/backups/logs``        db backup logs
``/srv/backups/duplicity``   filesystem backup configs/logs
============================ ==============================

Open db shell::

   $ sudo -u postgres psql

solr1
=====

=========================== =======================================
Location                    Description
=========================== =======================================
``/opt/solr``               solr installation
``/var/solr/data/planning`` configs and data for planning Solr core
``/srv/backups/logs``       backup logs
``/srv/backups/duplicity``  filesystem backup configs/logs
=========================== =======================================

Restart Solr::

   $ sudo service solr restart


***************************
Droplet Creation Parameters
***************************

db01 and db02
=============

=========== ==========================================================
Parameter   Value
=========== ==========================================================
Name        ``db01do.planning.org-live``, ``db02do.planning.org-live``
Resources   16 GB Memory / 320 GB Disk
Region      NYC2
Options     Private networking, Backups, Monitoring
SSH Key     imagescape@iscape
IPs         ``162.243.9.138``, ``162.243.12.101``
Private IPs ``10.128.21.233``, ``10.128.21.244``
=========== ==========================================================

web01 and web02
===============

=========== ============================================================
Parameter   Value
=========== ============================================================
Name        ``web01do.planning.org-live``, ``web02do.planning.org-live``
Resources   8 GB Memory / 160 GB Disk
Options     Private networking, Backups, Monitoring
SSH Key     imagescape@iscape
IPs         ``192.241.179.148``, ``192.241.185.8``
Private IPs ``10.128.3.251``, ``10.128.5.11``
=========== ============================================================

solr01
======

=========== =======================================
Parameter   Value
=========== =======================================
Name        ``solr01do.planning.org-live``
Resources   4 GB Memory / 80 GB Disk
Region      NYC2
Options     Private networking, Backups, Monitoring
SSH Key     imagescape@iscape
IPs         ``162.243.9.52``
Private IPs ``10.128.19.227``
=========== =======================================

*******************************
Ansible Provisioning Parameters
*******************************


commit: ``8113698187a2b56627e8778ff63d00f25eaf27aa``

.. highlight:: yaml

::

   - name: Base states
     hosts: web
     vars:
       - update_apt_cache: yes
     roles:
      - role: base
      - role: unattended
      - role: timezone
      - role: ntp
      - role: supervisor
      - role: nginx
      - role: letsencrypt
      - role: postfix
      - role: django
      - role: nrpe

    - name: Base states
      hosts: db
      vars:
       - update_apt_cache: yes
      roles:
       - role: base
       - role: unattended
       - role: timezone
       - role: ntp
       - role: supervisor
       - role: postfix
       - role: postgres
       - role: nrpe

    - name: Base states
      hosts: solr
      vars:
       - update_apt_cache: yes
      roles:
       - role: base
       - role: unattended
       - role: timezone
       - role: ntp
       - role: supervisor
       - role: postfix
       - role: nrpe


**************
Firewall Rules
**************

.. highlight:: bash


web1
====

::

   $ sudo iptables -S
   -P INPUT ACCEPT
   -P FORWARD ACCEPT
   -P OUTPUT ACCEPT
   -A INPUT -m state --state RELATED,ESTABLISHED -m comment --comment "allow established traffic" -j ACCEPT
   -A INPUT -i lo -m comment --comment "allow loopback" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 8080 -m comment --comment "allow nodejs traffic" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 80 -m comment --comment "allow http traffic" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 443 -m comment --comment "allow https traffic" -j ACCEPT
   -A INPUT -s 192.241.185.8/32 -p tcp -m comment --comment "Allow connections from web server" -j ACCEPT
   -A INPUT -s 38.124.64.143/32 -p icmp -m comment --comment "allow nagios ping" -j ACCEPT
   -A INPUT -s 38.124.64.143/32 -p tcp -m tcp --dport 22 -m comment --comment "allow nagios ssh" -j ACCEPT
   -A INPUT -s 38.124.64.143/32 -p tcp -m tcp --dport 5666 -m comment --comment "allow nagios nrpe" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 22 -m comment --comment "non-banned ssh traffic" -j ACCEPT
   -A INPUT -m comment --comment "drop everything else" -j DROP

web2
====

::

   $ sudo iptables -S
   -P INPUT ACCEPT
   -P FORWARD ACCEPT
   -P OUTPUT ACCEPT
   -A INPUT -m state --state RELATED,ESTABLISHED -m comment --comment "allow established traffic" -j ACCEPT
   -A INPUT -i lo -m comment --comment "allow loopback" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 8080 -m comment --comment "allow nodejs traffic" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 80 -m comment --comment "allow http traffic" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 443 -m comment --comment "allow https traffic" -j ACCEPT
   -A INPUT -s 192.241.179.148/32 -p tcp -m comment --comment "Allow connections from web server" -j ACCEPT
   -A INPUT -s 38.124.64.143/32 -p icmp -m comment --comment "allow nagios ping" -j ACCEPT
   -A INPUT -s 38.124.64.143/32 -p tcp -m tcp --dport 22 -m comment --comment "allow nagios ssh" -j ACCEPT
   -A INPUT -s 38.124.64.143/32 -p tcp -m tcp --dport 5666 -m comment --comment "allow nagios nrpe" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 22 -m comment --comment "non-banned ssh traffic" -j ACCEPT
   -A INPUT -m comment --comment "drop everything else" -j DROP

db1
===

::

   $ sudo iptables -S
   -P INPUT ACCEPT
   -P FORWARD ACCEPT
   -P OUTPUT ACCEPT
   -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
   -A INPUT -i lo -m comment --comment "allow loopback" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 5432 -m comment --comment "allow postgresql" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p icmp -m comment --comment "allow nagios ping" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p tcp -m tcp --dport 22 -m comment --comment "allow nagios ssh" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p tcp -m tcp --dport 5666 -m comment --comment "allow nagios nrpe" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 22 -m comment --comment "non-banned ssh traffic" -j ACCEPT
   -A INPUT -m comment --comment "drop everything else" -j DROP

db2
===

::

   $ sudo iptables -S:
   -P INPUT ACCEPT
   -P FORWARD ACCEPT
   -P OUTPUT ACCEPT
   -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
   -A INPUT -i lo -m comment --comment "allow loopback" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 5432 -m comment --comment "allow postgresql" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p icmp -m comment --comment "allow nagios ping" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p tcp -m tcp --dport 22 -m comment --comment "allow nagios ssh" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p tcp -m tcp --dport 5666 -m comment --comment "allow nagios nrpe" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 22 -m comment --comment "non-banned ssh traffic" -j ACCEPT
   -A INPUT -m comment --comment "drop everything else" -j DROP

   $ sudo iptables -S:
   -P INPUT ACCEPT
   -P FORWARD ACCEPT
   -P OUTPUT ACCEPT
   -A INPUT -s 192.241.179.148/32 -p tcp -m tcp --dport 8983 -m comment --comment "allow traffic from web1" -j ACCEPT
   -A INPUT -s 192.241.185.8/32 -p tcp -m tcp --dport 8983 -m comment --comment "allow traffic from web2" -j ACCEPT
   -A INPUT -s 96.95.110.221/32 -p tcp -m tcp --dport 8983 -m comment --comment "Allow iscape office for testing" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p icmp -m comment --comment "allow nagios ping" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p tcp -m tcp --dport 22 -m comment --comment "allow nagios ssh" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p tcp -m tcp --dport 5666 -m comment --comment "allow nagios nrpe" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 22 -m comment --comment "non-banned ssh traffic" -j ACCEPT
   -A INPUT -m comment --comment "drop everything else" -j DROP

solr1
=====



To add an IP address to the firewall rules on Solr (staging only, DO NOT change the firewall rules on prod), SSH in and run::

   $ sudo iptables -I INPUT 10 -p tcp -s <your ip address> --dport 8983 -j ACCEPT -m comment --comment "<my name> remote accesss"

The ``-I INPUT 10`` means to insert this rule at index 10 in the chain. This will not survive a reboot of the solr staging box (which should only happen after automatic kernel updates, so rarely, and we wouldn't want to keep random IPs in the whitelist anyway). You can print the list of rules with their line nubmers with::

   $ sudo iptables -L --line-numbers

To delete that rule::

   $ sudo iptables -D INPUT 10

::

   $ sudo iptables -S:
   -P INPUT ACCEPT
   -P FORWARD ACCEPT
   -P OUTPUT ACCEPT
   -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
   -A INPUT -i lo -m comment --comment "allow loopback" -j ACCEPT
   -A INPUT -s 192.241.179.148/32 -p tcp -m tcp --dport 8983 -m comment --comment "allow traffic from web1" -j ACCEPT
   -A INPUT -s 192.241.185.8/32 -p tcp -m tcp --dport 8983 -m comment --comment "allow traffic from web2" -j ACCEPT
   -A INPUT -s 96.95.110.221/32 -p tcp -m tcp --dport 8983 -m comment --comment "Allow iscape office for testing" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p icmp -m comment --comment "allow nagios ping" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p tcp -m tcp --dport 22 -m comment --comment "allow nagios ssh" -j ACCEPT
   -A INPUT -s 38.124.107.130/32 -p tcp -m tcp --dport 5666 -m comment --comment "allow nagios nrpe" -j ACCEPT
   -A INPUT -p tcp -m tcp --dport 22 -m comment --comment "non-banned ssh traffic" -j ACCEPT
   -A INPUT -m comment --comment "drop everything else" -j DROP

**********
Hosts File
**********

We made the following additions to the ``/etc/hosts`` file for easy access between the live web nodes::


   192.241.179.148   web01-live
   192.241.185.8     web02-live
   162.243.9.138     db01-live
   162.243.12.101    db02-live
   162.243.9.52      solr01-live

***************
GlusterFS Setup
***************

GlusterFS is in place to ensure that media files that are uploaded to one web server is propagated to the other. Gluster is installed on each web node and was installed via the following::

   $ sudo add-apt-repository ppa:gluster/glusterfs-3.8
   $ sudo apt-get update
   $ sudo apt-get install glusterfs-server
   $ sudo apt-get install glusterfs-client

On ``web01-live``::

   sudo gluster peer probe web01-live
   sudo gluster peer status

   # connect node 1 and node 2
   sudo gluster peer probe web02-live
   sudo gluster peer status

   # create a Gluster replica volume (only need to do this once)
   sudo gluster volume create volume1 replica 2 transport tcp \
         web01-live:/media \
         web02-live:/media force

   # list volumes
   sudo gluster volume list

   # start the gluster volume
   sudo gluster volume start volume1


On both web nodes::

   # mount the volume (do this on both web servers)
   sudo mount -t glusterfs planning-web01do:/volume1 /srv/sites/apa/htdocs/media/

**********
Solr Setup
**********

Installation::

   # prevent slow tomcat start
   apt-get install haveged

   sudo add-apt-repository ppa:webupd8team/java
   sudo apt-get update
   sudo apt-get install oracle-java8-installer

   cd ~
   wget http://www-eu.apache.org/dist/lucene/solr/5.5.5/solr-5.5.5.tgz
   tar xzf solr-5.5.5.tgz solr-5.5.5/bin/install_solr_service.sh --strip-components=2
   sudo chmod +x install_solr_service.sh
   sudo ./install_solr_service.sh solr-5.5.5.tgz

Create planning core::

   $ sudo -u solr ./solr create -c planning


Several configuration files were copied from the old production server::

   /var/solr/data/planning/conf/solrconfig.xml
   /var/solr/data/planning/conf/schema.xml
   /var/solr/data/planning/conf/elevate.xml
   /var/solr/data/planning/conf/currency.xml
   /var/solr/data/planning/conf/lang/*

Restart to reload configuration::

   $ sudo service solr restart


***************
Postgres Tuning
***************

.. highlight:: cfg

Adjusted ``/etc/postgresql/9.5/main/postgresql.conf`` with the following values::

   listen_address       = "*"
   work_mem             = 64MB
   maintenance_work_mem = 798MB
   shared_buffers       = 1996MB
   effective_cache_size = 3992MB
   random_page_cost     = 2.0

Added the following connecting settings to ``/etcpostgresql/9.5/main/pg_hba.conf``::

   hostssl   apa   apa   10.128.3.251/32    md5
   hostssl   apa   apa   10.128.21.244/32   md5
   host      apa   apa   10.128.3.251/32    md5
   host      apa   apa   10.128.21.244/32   md5

************
NodeJS Setup
************

.. highlight:: bash

Installation::

   $ curl -sL https://deb.nodesource.com/setup_6.x | sudo bash -
   $ sudo apt-get install nodejs

Nodejs is executed from a supervisor script located at /etc/supervisor/conf.d/node.conf. To restart nodejs, execute the following::

   $ sudo supervisorctl node restart

.. highlight:: cfg

Here is the supervisor configuration for this process::

   [program:node]
   command=node /srv/sites/apa/proj/planning/api_node/restify_server.js
   environment=NODE_ENV=/srv/sites/apa/proj/planning/api_node/node_modules/

   stderr_logfile=/srv/sites/apa/var/log/supervisor-node.stderr.log
   stdout_logfile=/srv/sites/apa/var/log/supervisor-node.stdout.log

   autorestart=true
   startretries=5
   autostart=true
   autorestart=unexpected
   user=planning


less Install
============

.. highlight:: bash

::

   $ sudo npm -g install npm@latest
   $ sudo npm install -g less


********************
Postgres Replication
********************

On db1::

   $ sudo -u postgres psql -c "CREATE USER rep REPLICATION LOGIN CONNECTION LIMIT 2 ENCRYPTED PASSWORD '<password in EPS>';"

.. highlight:: cfg

On db1 and db2, edit /etc/postgresql/9.5/main/postgresql.conf::

   listen_addresses  = '*'
   wal_level         = hot_standby
   archive_mode      = on
   max_wal_senders   = 2
   archive_command   = 'cd .'
   wal_keep_segments = 1000
   hot_standby       = on

.. highlight:: bash

On db2::

   $ sudo -s mv /var/lib/postgresql/9.5/main /var/lib/postgresql/9.5/main_old
   $ time sudo -u postgres pg_basebackup -h 10.128.21.233 \
                                         -D /var/lib/postgresql/9.5/main \
                                         -U rep \
                                         -vP \
                                         --xlog-method=stream

.. highlight:: cfg


Edit ``/var/lib/postgresql/9.5/main/recovery.conf``::

   standby_mode = 'on'
   primary_conninfo = 'host=10.128.21.233 user=rep password=<password>'
   trigger_file = '/tmp/postgresql.trigger.5432'


.. highlight:: bash

Be sure to restart the psotgresql service on both servers after updating configurations::

   $ sudo service postgresql restart


********************
Import Postgres Dump
********************


Locally::

   $ scp shemmy@107.170.185.114:/iscape/backups/database/planning_<current>.sq l.bz2 .
   $ scp planning_<current>.sql.bz2 shemmy@apa.db1

On db1::

   $ bunzip2 planning_<current>.sql.bz2

Had to do the following since the old db user is called "planning" rather than "apa"::

   $ sudo -u postgres psql

.. highlight:: psql

::

   CREATE ROLE planning;
   GRANT apa TO planning;
   ALTER ROLE planning WITH LOGIN;
   CREATE DATABASE apa WITH OWNER planning;

.. highlight:: bash

::

   $ sudo -u postgres psql apa < planning_<current>.sql


***************
PGBouncer Setup
***************

On both web nodes::

   $ sudo apt-get install pgbouncer

.. highlight:: cfg

Edit ``/etc/pgbouncer/pgbouncer.ini``::

   * = host=10.128.21.233 port=5432

   ; ip address or * which means all ip-s
   listen_addr = 127.0.0.1
   listen_port = 6432

.. highlight:: bash

::

   $ sudo cp /etc/pgbouncer/pgbouncer.ini /etc/pgbouncer/pgbouncer-slave.ini

.. highlight:: cfg

Edit ``/etc/pgbouncer/pgbouncer-slave.ini``::

   * = host=10.128.21.244 port=5432

   ; ip address or * which means all ip-s
   listen_addr = 127.0.0.1
   listen_port = 7432

   ; set up TLS/SSL
   server_tls_sslmode = require

.. highlight:: bash

Change permissions on the ini files::

   $ sudo chmod 644 /etc/pgbouncer/pgbouncer.ini
   $ sudo chmod 644 /etc/pgbouncer/pgbouncer-slave.ini
   $ sudo chown postgres:postgres /etc/pgbouncer/pgbouncer.ini
   $ sudo chown postgres:postgres /etc/pgbouncer/pgbouncer-slave.ini

Add db user to user list by editing ``/etc/pgbouncer/userlist.txt``::

   “planning” “md5< insert md5.hexdigest(username+password) >”


**********************************
Duplicity Filesystem Backups Setup
**********************************

Install necessary packages::

   $ sudo apt install mailutils s3cmd duplicity
   $ pip install boto

Create backup dir::

   $ sudo mkdir -p /srv/backups/duplicity
   $ sudo mkdir -p /srv/backups/duplicity/logs/
   $ sudo chmod g+s -R /srv/backups/
   $ sudo chgrp -R worker /srv/backups/

Get duplicity-backup.sh script::

   $ cd /srv/backups/duplicity
   $ git clone https://github.com/zertrin/duplicity-backup.git
   $ cd duplicity-backup
   $ cp duplicity-backup.conf.example duplicity-backup.conf

.. highlight:: cfg

Edit ``/srv/backups/duplicity/duplicity-backup.conf``::

   AWS_ACCESS_KEY_ID="get from eps"
   AWS_SECRET_ACCESS_KEY="get from eps"
   ENCRYPTION='no'
   ROOT="/"
   DEST="s3+http://planning.org-backups/00_system_backups/web01do-planning/"

   # Be caeful not to include ending slash, as that prevents the dir from being included
   # also be careful not to include a space at the end of the line (after the line break slash)
   # as that causes the script to fail
   INCLIST=( "/etc" )
   EXCLIST=()
   LOGDIR="/iscape/backups/duplicity/logs/"
   LOG_FILE="duplicity-`date +%Y-%m-%d_%H-%M`.txt"
   LOG_FILE_OWNER="apa:worker"
   EMAIL_TO="errors@imagescape.com"  # Change
   EMAIL_FROM="duplicity-backup-service@imagescape.com" # change
   EMAIL_SUBJECT="[Duplicity Service] Filesystem Backup Failed"

Also went into AWS and created new folders in the S3 buckets per the ``DEST`` variable on each server.

.. highlight:: bash

Add the following to the ``root`` crontab::

   $ sudo crontab -eu root

::

   # Run a duplicity FULL backup once daily on Sunday
   0 1 * * 0 /srv/backups/duplicity/duplicity-backup/duplicity-backup.sh -c
   /srv/backups/duplicity/duplicity-backup/duplicity-backup.conf --full

   # Run a duplicity INCREMENTAL backup once daily on Monday-Saturday
   0 1 * * 1,2,3,4,5,6 /srv/backups/duplicity/duplicity-backup/duplicity-backup.sh -c
   /srv/backups/duplicity/duplicity-backup/duplicity-backup.conf --backup

**************
RabbitMQ Setup
**************

Add ``rabbitmq`` repository to ``apt`` sources::

   $ sudo echo "deb http://www.rabbitmq.com/debian/ testing main" >> /etc/apt/sources.list
   $ sudo curl http://www.rabbitmq.com/rabbitmq-signing-key-public.asc | sudo apt-key add -

Install ``rabbitmq-server``::

   $ sudo apt-get update
   $ sudo apt-get install rabbitmq-server

Add a RabbitMQ user and vhost::

   $ sudo rabbitmqctl add_user apa <password>
   $ sudo rabbitmqctl add_vhost apa
   $ sudo rabbitmqctl set_user_tags apa apatag
   $ sudo rabbitmqctl set_permissions -p apa apa ".*" ".*" ".*"

************
Celery Setup
************

.. highlight:: cfg

Add or edit the Supervisor configuration file in ``/etc/supervisor/conf.d/celery.conf``::

   [program:celery]
   command=/srv/sites/apa/envs/apa/bin/celery worker -E -B -A planning.celery --loglevel=debug --concurrency=3 -Ofair
   environment=
      PATH="$PATH:/usr/bin/:/srv/sites/apa/envs/apa/bin/",
      PYTHONPATH="$PYTHONPATH:/srv/sites/apa/proj/apa/", autostart=true
   autorestart=unexpected
   user=apa

.. highlight:: python

In the code repo, edit ``planning/settings/local.py``::

   BROKER_URL = "amqp://apa:<password>@localhost:5672/apa"


*************
Hardening SSH
*************

.. highlight:: cfg

Change the following settings in ``/etc/sshd_config``::

   PermitRootLogin no
   PasswordAuthentication no

   # Ciphers/Key Algos, pulled from the Modern config from
   # https://infosec.mozilla.org/guidelines/openssh
   KexAlgorithms
   curve25519-sha256@libssh.org,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ec dh-sha2-nistp256,diffie-hellman-group-exchange-sha256
   Ciphers
   chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@opens sh.com,aes256-ctr,aes192-ctr,aes128-ctr
   MACs
   hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128- etm@openssh.com,hmac-sha2-512,hmac-sha2-256,umac-128@openssh.com
   HostKeyAlgorithms ssh-ed25519-cert-v01@openssh.com,ssh-rsa-cert-v01@openssh.com,ssh-ed2 5519,ssh-rsa,ecdsa-sha2-nistp521-cert-v01@openssh.com,ecdsa-sha2-nist p384-cert-v01@openssh.com,ecdsa-sha2-nistp256-cert-v01@openssh.com,ec dsa-sha2-nistp521,ecdsa-sha2-nistp384,ecdsa-sha2-nistp256


*******************
Hardening NGINX/SSL
*******************

We set up the NGINX config using the intermediate settings, ciphers, and protocols that can be found `here <https://mozilla.github.io/server-side-tls/ssl-config-generator/>`_.

We have not enabled HSTS as of this writing, as setting it up can be tricky and you could potentially lock yourself out of your domain if you do it wrong.


***********************************
Random Caveats with Running the App
***********************************

.. highlight:: bash

Needed odbc dev libraries for ``pyodbc`` requirement::

   $ sudo apt-get install unixodbc unixodbc-dev

Install requirements::

   $ venv apa
   $ cd /srv/sites/apa/proj/apa
   $ pip install -r requirements.txt

Add a ``local.py`` in ``srv/sites/apa/proj/apa/planning/settings`` and edit accordingly.

Install ``uwsgitop``::

   $ sudo pip install uwsgitop

On web1 and web2::

   $ cd /iscape/sites/planning/proj/planning_static_uploads/
   $ rsync -avz 159.203.164.77:/iscape/sites/planning/proj/planning_static_uploads/ planning_static_uploads
