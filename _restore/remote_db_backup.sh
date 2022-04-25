#!/bin/bash
# this script has been created to remotely backup the latest postgres db and 
# restore it to the development or staging database.

# new backup
if [ $2 == 2 ];
	then
		echo Dumping new backup to /tmp/remote_backup.sql.bz2
		sudo -u postgres pg_dump -v planning | bzip2 > /tmp/remote_backup.sql.bz2;

# overnight backup
else
	echo Copying the latest backup...
	cd /srv/backups/database
	TEST=`ls -Art | tail -n 1`
	echo $TEST
	sudo cp  /srv/backups/database/$TEST  /tmp/remote_backup.sql.bz2;
fi

echo Copying zipped backup to test server...
scp -i /home/dbrestore/.ssh/id_rsa /tmp/remote_backup.sql.bz2 dbrestore@$1:/tmp

echo Running restore script on remote server.
ssh -t -i /home/dbrestore/.ssh/id_rsa dbrestore@$1 "bash /opt/remote_db_restore.sh"
