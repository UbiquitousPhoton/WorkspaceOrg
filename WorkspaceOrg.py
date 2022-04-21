#!/usr/bin/env python3

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

import argparse

from windowmanager import *

from LoggerManager.loggermanager import Logger_Manager, Loglevel
from exceptions import *

from datetime import datetime
from time import sleep, time
from traceback import format_exc

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

    logger_manager = Logger_Manager()

    if args.verbose:
        logger_manager.setup_stdout(Loglevel.DEBUG)

    if args.logfile != None:
        logger_manager.setup_logfile(args.logfile, 2, Loglevel.INFO)

    try:
        win_manager = WindowManager(logger_manager)

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

                logger_manager.log(Loglevel.INFO, "### Loop {} start.".format(loop_counter))
                loop_counter = loop_counter + 1

                win_manager.get_window_details()

                win_manager.apply_rules()

                logger_manager.log(Loglevel.INFO,
                                   "### Sleeping for {} secs.".format(win_manager.sleep_time))

                sleep(win_manager.sleep_time)

                time_taken = time() - start_time;

    except ConfigError as e:
        logger_manager.log(Loglevel.ERROR, e.GetMessage())

    except GenericError as e:
        logger_manager.log(Loglevel.ERROR, e.GetMessage())

    except:
        logger_manager.log(Loglevel.ERROR, format_exc())

    finally:
        logger_manager.log(Loglevel.INFO, "### Script done.")

if __name__ == "__main__":
    exit(main())
