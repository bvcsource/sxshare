if [[ $VIRTUAL_ENV != "" ]]; then
    echo "deactivate first"
    exit 1
fi

source $(which virtualenvwrapper.sh)
rmvirtualenv sxshare
mkvirtualenv sxshare

set -e

echo "Installing python packages"
workon sxshare
pip install -r dev_requirements.txt

echo "All done"
