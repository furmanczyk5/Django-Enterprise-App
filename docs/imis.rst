####################
iMIS
####################

************
Environments
************

iMIS servers (web and database) are hosted on Microsoft Azure through RSM.


=====================================     ==================
Host Name                                 IP Address
=====================================     ==================
Staging
``devsql01.planning.org``                 ``157.55.213.171``
``staffdev.planning.org/imis_live/``      ``65.52.207.223``
Prod
``prodsql01.planning.org``                ``23.101.160.66``
``staff.planning.org/imis_live/``         ``162.243.12.101``
=====================================     ==================


***************
Service Tickets
***************


RSM should be contacted for any server related issues. A service ticket should be open for any non-critical problems or requests. Roy C., Phillip L., or Ran W. have authorization to create tickets in the `RSM Service Portal <https://rsmconnect.rsmus.com/v4_6_release/services/system_io/customerportal/portal.html?company=mcgladrey&locale=en#>`_

TO DO: Enter emergency phone number here.


***************************************
SQL Database Restore
***************************************

To perform a backup and restore you will need access to the production SQL server. Contact Phillip L. or Ran W. to have an RSM domain account created.

1. RDP into the production SQL server (prodsql01.planning.org).
2. Open Management Studio (shortcut on desktop), and login with your credentials to devsql01.planning.org.
3. Right click imis_live database. Go to Tasks - Restore - Database.
4. Change Source - Device. Change the backup device to File.
5. Navigate to D:/Backup/imis_live/. Select the latest backup.
6. Under the Options page, check "Overwrite the existing database (WITH REPLACE).
7. Under the Options page, check "Close existing connections to destination database".
8. Bam.

After the restore is complete, execute the following query to give the django user access on the restored test imis_live database::

    alter user [django] with login=[django];



***************************************
Best Practices and Standardizations
***************************************


Panels
======
Naming Convention
    Prefix with APA. If combining two data sources make sure the sources are in the name.

    Example: APA Race_Origin with Contact

Business Objects (BO)
=====================
Naming Convention
    For preferred replacements of an existing business object, append "_APA".
    Example: NetContact_APA

    For enhanced or improved version of a business object, append underscore with a short summary of what else it returns.
    Example: NetContact_WithEducation

    If the business object is completely custom, prefix it with "_APA" so it shows at the top of the list
    Example: _APA_Accredited_Schools

Content
=======
Naming Convention
    No standard convention. Name the content whatever it displays.

Intelligent Query Architect (IQA)
=================================
Naming Convention
    No standard conventions. Name the IQA whatever it returns.

File Location
    All custom APA IQAs should be stored under the _APA folder. There's a department folder for department specific IQAs, which is where most staff will be pulling their data from.
