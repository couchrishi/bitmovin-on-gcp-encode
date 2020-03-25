#!/bin/bash
file_name="utils"
infra_name=$1
infra_desc=$2
shift

pip3 install -r requirements.txt

PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PYTHONPATH
export infra_name
export infra_desc

#python3 "./src/$file_name.py" "$@"
python3 -c "import os, sys; import utils; utils.init_bitmovin_api(); infra = utils.create_gce_account(os.environ.get('infra_name'), os.environ.get('infra_desc')); print(infra);"
