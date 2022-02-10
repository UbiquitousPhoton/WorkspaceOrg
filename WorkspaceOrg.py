#!/usr/bin/env python3

#   MIT License
#
#   Copyright (c) 2021 Paul Elliott
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

import os
import argparse
import configparser
import toml
import sys
from subprocess import Popen, PIPE
from shlex import split
import LoggerManager.loggermanager as loggermanager
from exceptions import *
from enum import Flag, auto
from datetime import datetime
from time import sleep, time
from traceback import format_exc

class XWindow:

    def __init__(self, win_handle, desktop, pos_x, pos_y, size_x, size_y, win_type, description):
        self.win_handle = win_handle
        self.desktop = int(desktop)
        self.pos_x = int(pos_x)
        self.pos_y = int(pos_y)
        self.size_x = int(size_x)
        self.size_y = int(size_y)
        self.win_type = win_type
        self.description = description
        self.seen = True

    def __str__(self):
        return "Handle : {} | Workspace : {} | Type : {} | Pos {} x {} | Size {} x {} | Desc : {}".format(self.win_handle,
                                                                                                          self.desktop,
                                                                                                          self.win_type,
                                                                                                          self.pos_x,
                                                                                                          self.pos_y,
                                                                                                          self.size_x,
                                                                                                          self.size_y,
                                                                                                          self.description)

    def update(self, desktop, pos_x, pos_y, size_x, size_y, description):

        changed = False

        if self.desktop != int(desktop):
            self.desktop = int(desktop)
            changed = True

        if self.pos_x != pos_x:
            self.pos_x = pos_x
            changed = True

        if self.pos_y != pos_y:
            self.pos_y = pos_y
            changed = True

        if self.size_x != size_x:
            self.size_x = size_x
            changed = True

        if self.size_y != size_y:
            self.size_y = size_y
            changed = True

        if self.description != description:
            self.description = description
            changed = True

        self.seen = True

        return changed

class WindowRule:

    def __init__(self, name, desktop, pos_x, pos_y, size_x, size_y):
        self.name = name
        self.win_type = ""
        self.description = ""
        self.desktop = desktop
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.size_x = size_x
        self.size_y = size_y

        self.flags = 0

    def set_win_type(self, win_type):
        self.win_type = win_type;

    def set_win_description(self, win_description):
        self.description = win_description

class Desktop:

    """
    Desktop / Workspace container
    """

    def __init__(self, desktop_index, desktop_size, desktop_name):
        self.index = desktop_index
        self.name = desktop_name

        desktop_size_split = desktop_size.split("x")

        self.width = int(desktop_size_split[0])
        self.height = int(desktop_size_split[1])

    def __str__(self):
        return "Index : %d | Name %s | Dimensions : %d x %d" % (self.index,
                                                                self.name,
                                                                self.width,
                                                                self.height)


class XWindowManager:


    def __init__(self, logger_manager):
        self.win_dict = {}
        self.win_rules = []
        self.desktops = {}
        self.logger_manager = logger_manager


    def do_shell_exec(self, exec_string, expected_result = 0):

        """
        Helper function to do shell executions
        """

        shell_process = Popen(split(exec_string), stdin=PIPE, stdout=PIPE, stderr=PIPE)

        (shell_stdout, shell_stderr) = shell_process.communicate()

        if shell_process.returncode != expected_result:
            self.logger_manager.log(loggermanager.Loglevel.INFO,
                                    "{} returned {}".format(exec_string,
                                                            shell_process.returncode))
            logger_manager.log(loggermanager.Loglevel.INFO,
                               "stderr: {}".format(shell_stderr.decode("UTF-8")))
            return False, shell_stdout.decode("utf-8")

        else:
            return True, shell_stdout.decode("utf-8")

    def print(self):
        """
        Debug printing of Window Manager contents
        """
        for win_type in self.win_dict:
            for win in self.win_dict[win_type]:
                self.logger_manager.log(loggermanager.Loglevel.INFO, win)

    def has_win(self, win_type, win_handle):
        """
        Ascertain if we already have a window of a given type and handle.
        """
        if win_type in self.win_dict:
            for win in self.win_dict[win_type]:
                if win.win_handle == win_handle:
                    return True

        return False

    def add_or_update_window(self, win_handle, desktop, pos_x, pos_y, size_x, size_y, win_type,
                             description):

        """
        Add details for a new window, or update one we already knew about.
        """
        if win_type in self.win_dict:

            found = False

            for win in self.win_dict[win_type]:
                if win.win_handle == win_handle:
                    if win.update(desktop, pos_x, pos_y, size_x, size_y, description):
                        self.logger_manager.log(loggermanager.Loglevel.INFO,
                                                "updating {} : {}".format(win_handle, win_type))
                    found = True

            if(not found):
                self.logger_manager.log(loggermanager.Loglevel.INFO, "Adding {} : {}".format(win_handle,
                                                                               win_type))
                self.win_dict[win_type].append(XWindow(win_handle, desktop, pos_x, pos_y,
                                                       size_x, size_y,
                                                       win_type, description))
        else:
            self.win_dict[win_type] = []
            self.win_dict[win_type].append(XWindow(win_handle, desktop, pos_x, pos_y, size_x,
                                                   size_y, win_type, description))


    def get_desktop_details(self):

        """
        Get all currently configured desktops details.
        """
        success, output = self.do_shell_exec("wmctrl -d")

        if not success:
            raise GenericError("wmctrl -d returned {}".format(output))

        for line in output.splitlines():
            line_split = line.split()

            desktop_index = int(line_split[0])
            new_desktop = Desktop(desktop_index, line_split[3], line_split[len(line_split) - 1])
            self.desktops[desktop_index] = new_desktop;


    def get_desktop_index(self, desktop_name):

        """
        Get a desktop's index from its name, returns -1 if not found.
        """

        for desktop_index, desktop in self.desktops.items():
            if desktop.name == desktop_name:
                return desktop_index

        return -1

    def get_window_details(self):

        """
        Get details of all currently open windows via wmcrtrl
        """
        for win_type in self.win_dict:
            for win in self.win_dict[win_type]:
                win.seen = False

        success, output = self.do_shell_exec("wmctrl -lxG")

        if not success:
            raise GenericError("wmctrl -lxG returned {}".format(output))

        for line in output.splitlines():
            line_split = line.split(maxsplit=8)

            # Dialogs do not have titles / descriptions
            win_title = ""
            if len(line_split) > 8:
                win_title = line_split[8]

            self.add_or_update_window(line_split[0], line_split[1], line_split[2],
                                      line_split[3], line_split[4], line_split[5], line_split[6],
                                      win_title)

        # remove any windows that have disappeared since last update
        for win_type in self.win_dict:
            for win_count, win in enumerate(self.win_dict[win_type]):
                if not win.seen:
                    self.logger_manager.log(loggermanager.Loglevel.DEBUG,
                                            "removing {} as not found".format(win.win_handle))
                    self.win_dict[win_type].pop(win_count)

    def dump_window_details(self, dump_file):

        """
        Dump all window details into a config file
        """

        out_dict = {}
        apps_dict = {}

        for window_type in self.win_dict:

            for window_count, window in enumerate(self.win_dict[window_type], start = 1):

                if len(self.win_dict[window_type]) > 1:
                    apps_dict["{}_{}".format(window.win_type,
                                             window_count)] = { "Type": window.win_type,
                                                                "Description": window.description,
                                                                "Desktop": window.desktop,
                                                                "Pos_x": window.pos_x,
                                                                "Pos_y": window.pos_y,
                                                                "Size_x": window.size_x,
                                                                "Size_y": window.size_y}
                else:
                    apps_dict[window.win_type] = { "Type": window.win_type,
                                                   "Description": window.description,
                                                   "Desktop": window.desktop,
                                                   "Pos_x": window.pos_x,
                                                   "Pos_y": window.pos_y,
                                                   "Size_x": window.size_x,
                                                   "Size_y": window.size_y}

                # TODO - Flags?

        out_dict["Apps"] = apps_dict

        with open(dump_file, "w") as file:
            toml.dump(out_dict, file)

    def get_config_options(self, config_file):

        """
        Get options / rules from the supplied config file.
        """

        with open(config_file) as file:
            config = toml.load(file)

        # Global setup variables.
        self.max_run_time = config['Setup'].get("MaxTime", 60)
        self.sleep_time = config['Setup'].get("SleepTime", 5)

        programs = config.get("Apps", {})

        if programs is None:
            raise ConfigError("No app rules in config file")


        for item in programs:

            rule_type = config['Apps'][item].get("Type", "")
            rule_description = config['Apps'][item].get("Description", "")

            if not rule_type and not rule_description:
                raise ConfigError("Missing type or description entry in {} rule".format(item))

            config_desktop = config['Apps'][item].get("Desktop", -1)

            if type(config_desktop) == int:
                rule_desktop = config_desktop

                if rule_desktop == -1:
                    raise ConfigError("Missing desktop entry in {} rule".format(config_desktop,
                                                                                item))
            else:
                rule_desktop = self.get_desktop_index(config_desktop)

                if rule_desktop == -1:
                    raise ConfigError("Unknown desktop {} in {} rule".format(config_desktop,
                                                                             item))

            rule_posx = config['Apps'][item].get("Pos_x", -1)

            if type(rule_posx) not in {int, float}:
                raise ConfigError("Unknown Pos_x ({}) in {} rule".format(rule_posx,
                                                                         item))

            rule_posy = config['Apps'][item].get("Pos_y", -1)

            if type(rule_posy) not in {int, float}:
                raise ConfigError("Unknown Pos_y ({}) in {} rule".format(rule_posy,
                                                                         item))

            rule_sizex = config['Apps'][item].get("Size_x", -1)

            if type(rule_sizex) not in {int, float}:
                raise ConfigError("Unknown Size_x ({}) in {} rule".format(rule_sizex,
                                                                          item))
            rule_sizey = config['Apps'][item].get("Size_y", -1)

            if type(rule_sizey) not in {int, float}:
                raise ConfigError("Unknown Size_y ({}) in {} rule".format(rule_sizey,
                                                                          item))

            rule_flags = config['Apps'][item].get("Flags", {})

            new_rule = WindowRule(item, rule_desktop, rule_posx, rule_posy, rule_sizex, rule_sizey,
                                  rule_flags)

            if rule_type:
                new_rule.set_win_type(rule_type)

            if rule_description:
                new_rule.set_win_description(rule_description)

            self.logger_manager.log(loggermanager.Loglevel.INFO,
                                    "Adding rule {} - type {}, description {} => {}".format(item,
                                                                                            rule_type,
                                                                                            rule_description,
                                                                                            rule_desktop))

            self.win_rules.append(new_rule)

    def apply_rules(self):

        """
        Apply the rules we got from the config file.
        """

        for rule in self.win_rules:
            for win_type in self.win_dict:
                if win_type.find(rule.win_type) != -1:
                    self.logger_manager.log(loggermanager.Loglevel.INFO, "found {}".format(rule.win_type))

                    for win in self.win_dict[win_type]:
                        if rule.description == "" or rule.description in win.description:

                            if win.desktop != rule.desktop:
                                self.logger_manager.log(loggermanager.Loglevel.DEBUG,
                                                        "moving {} to {}".format(rule.win_type,
                                                                                 rule.desktop))

                                success, \
                                    output = self.do_shell_exec("wmctrl -i -r {} -t {}".format(win.win_handle,
                                                                                               rule.desktop))

                                win.desktop = rule.desktop
                                # if any output at all, this failed.
                            else:
                                self.logger_manager.log(loggermanager.Loglevel.DEBUG,
                                                        "{} already on {}".format(rule.win_type,
                                                                                     win.desktop))



                            # Get desktop to work out absolute sizes (if required)
                            desktop_width = self.desktops[win.desktop].width
                            desktop_height = self.desktops[win.desktop].height

                            if type(rule.pos_x) == float:
                                if rule.pos_x >= 0.0:
                                    pos_x = int(desktop_width * rule.pos_x) + 4
                                else:
                                    pos_x = -1
                            else:
                                pos_x = rule.pos_x

                            if type(rule.pos_y) == float:
                                if rule.pos_y >= 0.0:
                                    pos_y = int(desktop_height * rule.pos_y) + 4
                                else:
                                    pos_y = -1
                            else:
                                pos_y = rule.pos_y

                            if type(rule.size_x) == float:
                                if rule.size_x >= 0.0:
                                    size_x = int(desktop_width * rule.size_x) - 8
                                else:
                                    size_x = -1
                            else:
                                size_x = rule.size_x

                            if type(rule.size_y) == float:
                                if rule.size_y >= 0.0:
                                    size_y = int(desktop_height * rule.size_y) - 8
                                else:
                                    size_y = -1
                            else:
                                size_y = rule.size_y

                            if pos_x != -1 or pos_y != -1 or \
                                size_x != -1 or size_y != -1:
                                if win.pos_x != pos_x or win.pos_y != pos_y or win.size_x \
                                    != size_x or win.size_y != size_y:

                                    success, \
                                        output = self.do_shell_exec("wmctrl -i -r {} -e 0,{},{},{},{}".format(win.win_handle,
                                                                                                              pos_x,
                                                                                                              pos_y,
                                                                                                              size_x,
                                                                                                              size_y))

                                    self.logger_manager.log(loggermanager.Loglevel.INFO,
                                                            "moving {} to ({}x{}) - size ({}x{})".format(rule.win_type,
                                                                                                         pos_x,
                                                                                                         pos_y,
                                                                                                         size_x,
                                                                                                         size_y))
def main():

    parser = argparse.ArgumentParser(description='Move certain window types / descriptions onto specified workspaces')
    parser.add_argument('-i', '--input', help='Input config file')
    parser.add_argument('-o', '--output', help='Rules dump output file')
    parser.add_argument('-l', '--logfile', help='File to log to')
    parser.add_argument('-v', '--verbose', action='store_true', help='Log to standard out')

    args = parser.parse_args()

    if args.input == None and args.output == None:
        print("Either --input or --output is required")
        return

    logger_manager = loggermanager.Logger_Manager()

    if args.verbose:
        logger_manager.setup_stdout(loggermanager.Loglevel.DEBUG)

    if args.logfile != None:
        logger_manager.setup_logfile(args.logfile, 2, loggermanager.Loglevel.DEBUG)

    try:
        win_manager = XWindowManager(logger_manager)

        win_manager.get_desktop_details()

        if args.output != None:
            win_manager.get_window_details()
            win_manager.dump_window_details(args.output)

        if args.input != None:

            win_manager.get_config_options(args.input)

            start_time = time()
            time_taken = 0.0
            loop_counter = 0

            while time_taken < win_manager.max_run_time:

                logger_manager.log(loggermanager.Loglevel.INFO, "### Loop {} start.".format(loop_counter))
                loop_counter = loop_counter + 1

                win_manager.get_window_details()

                win_manager.apply_rules()

                logger_manager.log(loggermanager.Loglevel.INFO,
                                   "### Sleeping for {} secs.".format(win_manager.sleep_time))

                sleep(win_manager.sleep_time)

                time_taken = time() - start_time;

    except ConfigError as e:
        logger_manager.log(loggermanager.Loglevel.ERROR, e.GetMessage())

    except GenericError as e:
        logger_manager.log(loggermanager.Loglevel.ERROR, e.GetMessage())

    except:
        logger_manager.log(loggermanager.Loglevel.ERROR, format_exc())

    finally:
        logger_manager.log(loggermanager.Loglevel.INFO, "### Script done.")

if __name__ == "__main__":
    exit(main())
