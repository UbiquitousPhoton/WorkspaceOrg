#   MIT License
#
#   Copyright (c) 2022 Paul Elliott
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

from utils import *
from exceptions import *
from windowmanager import *
import toml

class Config:

    """
    Class defining a connected monitor, in order to attempt to identify
    different hardware setups for (say) a laptop. Data collected via xrandr
    """

    def __init__(self, max_run_time, sleep_time, demaximise):
        self.max_run_time = max_run_time
        self.sleep_time = sleep_time
        self.demaximise = demaximise

        self.win_rules = []

    def add_rule(self, rule):
        self.win_rules.append(rule)

class ConfigManager:

    def __init__(self, logger_manager, window_manager):
        self.logger_manager = logger_manager
        self.window_manager = window_manager

        self.config = None

    def get_active_config(self):

        return self.config

    def get_config_options(self, config_file):

       """
       Get options / rules from the supplied config file.
       """

       with open(config_file) as file:
           config = toml.load(file)

       # Global setup variables.
       self.config = Config(config['Setup'].get("MaxTime", 60),
                            config['Setup'].get("SleepTime", 5),
                            config['Setup'].get("Demaximise", False))

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
               rule_desktop = self.window_manager.get_desktop_index(config_desktop)

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

           flags = WindowFlag.NONE
           rule_flags = config['Apps'][item].get("Flags", "")

           if rule_flags.lower() == "maximised" or rule_flags.lower() == "maximized":
               flags |= WindowFlag.MAXIMISED
           if rule_flags.lower() == "maxvertical":
               flags |= WindowFlag.MAX_VERTICAL
           if rule_flags.lower() == "maxhorizontal":
               flags |= WindowFlag.MAX_HORIZONTAL

           new_rule = WindowRule(item, rule_desktop, rule_posx, rule_posy, rule_sizex,
                                 rule_sizey,
                                 flags)

           if rule_type:
               new_rule.set_win_type(rule_type)

           if rule_description:
               new_rule.set_win_description(rule_description)

           self.logger_manager.log(Loglevel.INFO,
                                   "Adding rule {} - type {}, description {} => {}".format(item,
                                                                                           rule_type,
                                                                                           rule_description,
                                                                                           rule_desktop))

           self.config.add_rule(new_rule)

