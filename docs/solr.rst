Solr Search Engine
==================

We use Apache solr to search content on planning.org. Solr is installed
on a separate droplet than our webserver, and requires us to separately
publish content to solr so that it is searchable.

Publishing Schema Changes
-------------------------

The solr schema is an xml file that defines how data is storeed and
queried in solr. We often need to make updates to what data/fields are
searchable, what data is returned in search results, etc.

A copy of our schema exists within our planning.org project repository
(``_solr/schema.xml``)

After making changes to this file, they must be pushed to the solr
server. Unlike our webserver, the solr search does not read this file
from our Github repository.

The following is not the only way to make changes to our schema, but it
is what I have found easy in the past.

Install and configure sftp/ftp plugin for Sublime Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I generally work in sublime text though any ftp/sftp software or even
using ftp from the terminal should work

Installation
^^^^^^^^^^^^

1. Open Sublime Text

2. Open the package manager (COMMAND + SHIFT + P)

3. Search and select “Package Control: Install Package”

4. Search and select the packaged named “SFTP”

Configuration
^^^^^^^^^^^^^

1. Within Sublime Text, right click the file (``_solr/schema.xml``) or
   folder that you want to create remote ftp mapping for, and choose
   “SFTP/FTP” > “Map to Remote…”.

2. You should now be editing a configuration json file for the remote
   mapping. Here is an example of what this should look like when
   complete.

   .. code:: javascript

      {
      // The tab key will cycle through the settings when first created
      // Visit http://wbond.net/sublime_packages/sftp/settings for help
      // sftp, ftp or ftps
      "type": "sftp",

      "save_before_upload": true,
      "upload_on_save": false,
      "sync_down_on_open": false,
      "sync_skip_deletes": false,
      "sync_same_age": true,
      "confirm_downloads": false,
      "confirm_sync": true,
      "confirm_overwrite_newer": false,

      "host": "192.241.167.78",
      "user": "root",
      //"password": "password", // NOTE... if we want to specify password here, then we should ignore this file from source control


      "remote_path": "/var/solr/data/planning/conf/",
      "ignore_regexes": [
          "\\.sublime-(project|workspace)", "sftp-config(-alt\\d?)?\\.json",
          "sftp-settings\\.json", "/venv/", "\\.svn/", "\\.hg/", "\\.git/",
          "\\.bzr", "_darcs", "CVS", "\\.DS_Store", "Thumbs\\.db", "desktop\\.ini"
      ],


      "connect_timeout": 30,

      }

3. Create multiple mappings to easily switch between staging
   (192.241.167.78) and production (162.243.21.136).

Publish schema changes
~~~~~~~~~~~~~~~~~~~~~~

1. After saving changes to your local copy, first make sure you are
   using the correct remote mapping. Right click schema.xml > “SFPT/FTP”
   > “Switch Remote Mapping”.
2. Then push schema.xml to remote. Right click schema.xml > “SFPT/FTP” >
   “Sync Local -> Remote”. In the console you will be prompted to enter
   a password for the user specified in sftp-config.json.
3. Finally we need to restart the solr server for changes to apply.
   Simply go to this link to restart staging,
   http://192.241.167.78:8983/solr/admin/cores?action=RELOAD&core=planning.
   Substitute the ip to restart Solr production.

Reindexing Solr Records
-----------------------

Immediately after publishing schema changes, existing data in solr will
not reflect schema changes until records are re-published to solr. There
are serveral scripts in ``_data_tools/solr_reindex.py`` for reindexing
content on planning.org. For example to reindex all jobs, ssh into one
of our web servers, open a django shell session, and run
``reindex_jobs()``.

Solr Dashboard
--------------

-  Staging: http://192.241.167.78:8983/solr/#/
-  Production: http://162.243.21.136:8983/solr/#/
-  Querying http://192.241.167.78:8983/solr/#/planning/query

   -  Useful for testing query syntax or viewing records

-  Logging http://192.241.167.78:8983/solr/#/~logging

   -  For debugging

-  Restarting

   -  Directly hit this link
      http://192.241.167.78:8983/solr/admin/cores?action=RELOAD&core=planning…
   -  …or click reload button from here
      http://192.241.167.78:8983/solr/#/~cores/planning

Re-indexing with nohup
----------------------

To reindex as a nohup script – will continue after closing terminal
window

In ``solr_reindex.py`` choose method (which records you want to reindex)

Change method call in ``reindex_solr.py`` to that method, then:

1. ssh into server
2. ``sudo nohup chown tjohnson nohup.out``
3. ``nohup ./manage.py shell < _data_tools/reindex_solr.py &``
