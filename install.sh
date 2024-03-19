#!/usr/bin/bash

[ "$UID" -eq 0 ] || exec sudo "$0" "$@"
USER_DIR="$(getent passwd $SUDO_USER | cut -d: -f6)"
WORKING_FOLDER="${USER_DIR}/homebrew/plugins/steam-deck-battery-tracker"

# Clean directory
mkdir -p /tmp/steam-deck-battery-tracker || true
pushd /tmp/steam-deck-battery-tracker
rm -rf *

systemctl stop plugin_loader || true
curl -L https://raw.githubusercontent.com/Legion-is-life/legion-go-battery-tracker/main/main.py -o main.py
curl -L https://github.com/Alexey-Batishcev/rog-ally-battery-tracker/releases/latest/download/index.js -o index.js

echo "Copying files..."
cp main.py $WORKING_FOLDER/
cp index.js $WORKING_FOLDER/dist/

systemctl start plugin_loader || true
echo "Successfully installed patched steam-deck-battery-tracker for Lenovo Legion Go!"