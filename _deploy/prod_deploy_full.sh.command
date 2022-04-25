# change directory to _deploy
# "full" deploy option also runs commands to collect static files and restart celery

cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

bash deploy_branch.sh normal prod full
