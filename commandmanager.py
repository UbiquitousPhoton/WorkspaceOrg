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

from enum import Flag, auto
import toml
from LoggerManager.loggermanager import Logger_Manager, Loglevel
from utils import *
from exceptions import *

class CommandManager:

    def __init__(self, logger_manager):
        self.logger_manager = logger_manager
        self.config_manager = None

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager

    def launch(self):

        """
        Launch commands
        """

        config = self.config_manager.get_active_config()

        for cmd in config.commands:
            self.logger_manager.log(Loglevel.INFO,
                                    "launching \"{}\"".format(cmd))

            success, \
                output = do_shell_exec("{}".format(cmd))
            if not success:
               raise GenericError("Command {} failed : %s".format(cmd, output))
