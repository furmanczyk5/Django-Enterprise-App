SERVER_NAME="Postgres"
PRODUCTION_DB_SERVER="162.243.9.138"
# get current directory to to get local users:
# is this too hacky?
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source "$DIR"/local_settings.sh

# change directory to repo root
echo "user name" 
echo "$deploy_user"
echo "Enter number for Postgres database to restore."
echo "[1] Development"
echo "[2] Staging"
read DATABASE

if [ $DATABASE != 1 ] && [ $DATABASE != 2 ]
	then  
		echo "You entered an invalid number." 
else
	if [ $DATABASE == 1 ] 
		then
			DATABASE_IP="192.241.175.29" # development
			DATABASE_NAME="DEVELOPMENT"
	else [ $DATABASE == 2 ]
			DATABASE_IP="162.243.4.129" # staging
			DATABASE_NAME="STAGING"
	fi

	echo "Which backup would you like to use?"
	echo "[1] Overnight backup (quick restore)"
	echo "[2] New backup (slow restore)"
	read RESTORE_TYPE

	if [ $RESTORE_TYPE == 1 ]
		then
			RESTORE_TYPE_NAME="overnight backup"
	elif [ $RESTORE_TYPE == 2 ]
		then
			RESTORE_TYPE_NAME="new backup"
	else
		echo "Invalid number entered. exiting."
		exit
	fi

	echo "Restoring PRODUCTION $SERVER_NAME to $DATABASE_NAME with restore type: $RESTORE_TYPE_NAME."
	echo "To continue type 'restore' (without quotes)"
	read USER_ACCEPT

	if [ "$USER_ACCEPT" == "restore" ]
		then
			echo "SSHing into $SERVER_NAME production server."
			ssh -t $deploy_user@$PRODUCTION_DB_SERVER "sudo bash /opt/remote_db_backup.sh $DATABASE_IP $RESTORE_TYPE"
		else
			echo "Canceled restore. Expected the word restore. You typed $USER_ACCEPT . Learn to spell."
	fi
fi
exit
# else
# 	echo "Invalid server. You entered $SERVER. Try entering a digit dummy."
# 	exit
# fi
