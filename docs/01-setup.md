
# Project Setup
* Use the following script to 
  - Create a new project directory
  - Create a virtual environment for the project
  - Activate the venv
  - Install required software
* Use the command ***deactivate*** to deactivate the environment

```bash
#!/usr/bin/env bash

cd ~/
PROJECT_DIR="$HOME/prgms/Python/neopixel-01"

# Create a project directory
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create a virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Now install the library
pip install rpi-ws281x

# Print message
echo -e "Don't for to use `sudo ./.venv/bin/python blink.py` to execute!\n`

```
