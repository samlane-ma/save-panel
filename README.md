# Budgie Panel Backup
### Simple Python script to save the current Budgie panel layout
### (Not extensively tested)

Usage:

`./save-budgie-panel -o panel.ini`

(using without the -o option will output to the console)

### Purpose:

Running `budgie-panel --reset --replace` resets the Budgie Panel to the default layout provided by the panel.ini file.

On Ubuntu, this can be found in `/usr/share/budgie-desktop/panel.ini`

This script will back up your current panels and applet layouts to a custom .ini file. If this file is copied to that folder, running `budgie-panel --reset --replace` will restore the panels to the backed up layout.

Back up the current panel.ini just in case.

Not all settings will be (or can be) restored. On older versions of Budgie Desktop, only the size, position, and applet layout can be restored. On newer versions, other options such as transparency, autohide, dock mode, shadow, and spacing can be restored.