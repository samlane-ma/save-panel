#!/usr/bin/env python3

import gi.repository
from gi.repository import Gio
import copy
import sys
import getopt
import subprocess

base_schema = "com.solus-project"
panel_schema = base_schema + ".budgie-panel"
panel_path = "/com/solus-project/budgie-panel/"

SECTIONS = [ 'start', 'center', 'end' ]

PANELDATA = { "top": { 'name': 'Top Panel', 'id': 'Top' },
              "left": { 'name': 'Left Panel', 'id': 'Left' },
              "right": { 'name': 'Right Panel', 'id': 'Right' },
              "bottom": { 'name': 'Bottom Panel', 'id': 'Bottom' } }


class BudgiePanel:

    def __init__(self, position, size, transparency, shadow, dock, spacing, autohide):
        self.position = position
        self.size = size
        self.transparency = transparency
        self.shadow = shadow
        self.dock = dock
        self.spacing = spacing
        self.autohide = autohide
        self.applets = []
    
    def count(self, search):
        count = 0
        for item in self.applets:
            if item[2] == search:
                count += 1
        return count


def get_has_extra_options():
    try:
        output = subprocess.run(["budgie-desktop", "--version"], capture_output=True)
        version = output.stdout.decode().splitlines()[0].split(" ")[1]
    except:
        version = "10.0.0"
    
    version = list(map(int, version.split(".")))
    if version[0] < 10:
        return False
    if version[1] < 7:
        return False
    return True


def get_panel_list(panel_info):
    data = []
    panel_list = []
    for each in panel_info:
        panel_list.append(PANELDATA[each.position]["name"])
    data.append("[Panels]")
    data.append("Panels=" + ";".join(panel_list))
    data.append("")
    return(data)


def get_panel_layout(panel, extraoptions):
    data = []
    data.append("[" + PANELDATA[panel.position]["name"] + "]")
    children = []
    for applet in panel.applets:
        children.append(applet[3])
    if len(children) > 0:
        data.append("Children=" + ";".join(children) + ";")
    data.append("Position=" + PANELDATA[panel.position]["id"])
    data.append("Size=" + str(panel.size))

    if extra_options:
        # Not used in earlier versions of Budgie Desktop
        data.append("Transparency=" + panel.transparency.lower())
        data.append("Autohide=" + panel.autohide.lower())
        data.append("Shadow=" + str(panel.shadow).lower())
        data.append("Spacing=" + str(panel.spacing))
        data.append("Dock=" + str(panel.dock).lower())

    data.append("")
    for applet in panel.applets:
        data.append("[" + applet[3] + "]")
        data.append("ID=" + applet[2])
        data.append("Alignment=" + SECTIONS[applet[0]])
        data.append("")
    return(data)


def get_applet_info(active_applets):
    found_applets = []
    for app in active_applets:
        curr_apppath = panel_path + "applets/{" + app + "}/"
        curr_app_settings = Gio.Settings.new_with_path(panel_schema + ".applet", curr_apppath)
        name = curr_app_settings.get_string("name")
        position = curr_app_settings.get_int ("position")
        alignment = curr_app_settings.get_string("alignment")
        found_applets.append([SECTIONS.index(alignment), position, name])
    found_applets.sort(key=lambda row: (row[0], row[1]))
    return found_applets

def add_unique_applet_name(panel):
    names = copy.deepcopy(panel.applets)
    # Gotta find a better way, but we need to create a unique name for the applets and append it
    # to the applet list. The issue is if an applet occurs more than once (such as spacer), we need
    # to number them (i.e. Spacer 1, Spacer 2, etc...). So we look for duplicate applets, and if
    # found, we change their name to number them.
    dupes = []
    for item in panel.applets:
        check = item[2]
        if panel.count(check) > 1 and not check in dupes:
            dupes.append(check)
    for item in dupes:
        suffix = 1
        for index, applet in enumerate(panel.applets):
            if applet[2] == item:
                names[index][2] = item + " " + str(suffix)
                suffix += 1
    for index, item in enumerate(panel.applets):
        item.append(names[index][2])
    return panel


def get_panel_info(extra_options):
    # Returns the UUIDs of all applets with the given name currently on the panel
    all_panels = []
    panel_settings = Gio.Settings(schema=panel_schema)
    allpanels_list = panel_settings.get_strv("panels")
    for p in allpanels_list:
        # Search each Budgie Panel and get a list of all the installed applets
        curr_panel_path = panel_path + "panels/{" + p + "}/"
        curr_panel_subject_settings = Gio.Settings.new_with_path(panel_schema + ".panel", curr_panel_path)
        active_applets = curr_panel_subject_settings.get_strv("applets")
        location = curr_panel_subject_settings.get_string("location")
        size = curr_panel_subject_settings.get_int("size")

        # following arent used in older panel.ini but are still available
        transparency = curr_panel_subject_settings.get_string("transparency")
        shadow = curr_panel_subject_settings.get_boolean("enable-shadow")
        dock = curr_panel_subject_settings.get_boolean("dock-mode")
        autohide = curr_panel_subject_settings.get_string("autohide")

        if extra_options:
            # spacing key is not in earlier versions of Budgie Desktop so it will crash
            # hard if we check this on those versions
            spacing = curr_panel_subject_settings.get_int("spacing")
        else:
            spacing = 5

        this_panel = BudgiePanel(location, size, transparency, shadow, dock, spacing, autohide)
        this_panel.applets = get_applet_info(active_applets)
        this_panel = add_unique_applet_name(this_panel)

        all_panels.append(this_panel)

    return all_panels


if __name__ == "__main__":

    argv = sys.argv[1:]
    output_file = ""

    try:
        opts, args = getopt.getopt(argv, "o:", 
                                   ["output ="])
    except:
        print("usage: ", sys.argv[0], "-o <filename>")
        sys.exit(2)
  
    for opt, arg in opts:
        if opt in ['-o', '--output']:
            output_file = arg
      
    extra_options = get_has_extra_options()
    panel_info = get_panel_info(extra_options)
    header = get_panel_list(panel_info)

    output = []

    for line in header:
        output.append(line)
    for panel in panel_info:
        panel_body = get_panel_layout(panel, extra_options)
        for line in panel_body:
            output.append(line)
    
    if output_file == "":
        for line in output:
            print(line)
    else:
        try:
            with open(output_file, "w") as panel_file:
                for line in output:
                    panel_file.write(f'{line}\n')
        except:
            print ("Error writing to ", output_file)
            exit(1)
