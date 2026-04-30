#!/usr/bin/env bash

set -euo pipefail

cd ~/
PROJECT_DIR="$HOME/prgms/Python/neopixel-01"

# Create a project directory
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create a virtual environment
rm -rf .venv
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Now install the library
pip install --upgrade pip
pip install --upgrade rpi-ws281x

# Record the present state of the venv
PKG_LIST="requirements.txt" > "docs/$PKG_LIST"         # clobber the old file
echo -e "# file: ${PKG_LIST}" >> "./docs/${PKG_LIST}"
echo -e "# \n# $(date)\n#" >> "./docs/${PKG_LIST}"
pip freeze | tee -a "./docs/${PKG_LIST}"

# Print message
echo -e "\nDon't forget to use \`sudo ./.venv/bin/python neo_monitor_01.py\` to execute!\n"


