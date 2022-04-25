# this script has been created to remotely restore the postgres backup to the dev or staging database.

echo unziping the backup remote_backup.sql.bz2 to remote_backup.sql
echo NOTE: Have patience! takes a minute...
bunzip2 -v -f /tmp/remote_backup.sql.bz2


# give dbrestore the ability to drop and recreate databases in postgres
echo  Dropping all connections from Postgres...
psql apa -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'apa' AND pid <> pg_backend_pid();"

echo Dropping planning DB...
dropdb apa

echo Creating planning DB...
createdb apa

echo Restoring planning DB from backup...
psql apa < /tmp/remote_backup.sql

echo Restore complete!
