clear

# change directory to _deploy
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# get the local settings
source local_settings.sh

# change directory to repo root
cd ..

#activate virtual environment
source $venv_path/bin/activate

# run tests
python manage.py test