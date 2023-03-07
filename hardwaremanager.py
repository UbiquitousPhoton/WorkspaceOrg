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

class Monitor:

    """
    Class defining a connected monitor, in order to attempt to identify
    different hardware setups for (say) a laptop. Data collected via xrandr
    """

    def __init__(self, connector, hardware_id, size_x, size_y,
                 offset_x, offset_y):
        self.connector = connector
        self.hardware_id = hardware_id
        self.size_x = size_x
        self.size_y = size_y
        self.offset_x = offset_x
        self.offset_y = offset_y

    def __str__(self):
        return "Connector : {} | Hardware Id {} | Size : {}x{} | Offset {}x{}".format(self.connector,
                                                                                      self.hardware_id,
                                                                                      self.size_x,
                                                                                      self.size_y,
                                                                                      self.offset_x,
                                                                                      self.offset_y)


class HardwareManager:

    """
    Class to detect and match current hardware setup in order to choose between
    various setups
    """

    def __init__(self, logger_manager):
         self.monitors = {}
         self.logger_manager = logger_manager

    def get_hardware_setup(self):

        self.get_attached_monitors()


    def get_attached_monitors(self):

        success, output = do_shell_exec("xrandr --props")

        if not success:
            raise GenericError("xrandr failed : {}".format(output))

        waiting_edid_marker = False
        waiting_edid = False

        for line in output.splitlines():
            line_split = line.split()

            if len(line_split) > 2 and line_split[1] == "connected":
                connection_name = line_split[0]

                if line_split[2] == "primary":
                    monitor_dimensions = line_split[3]
                else:
                    monitor_dimensions = line_split[2]

                waiting_edid_marker = True

            if waiting_edid_marker and line_split[0] == "EDID:":
                waiting_edid_marker = False
                waiting_edid = True

            elif waiting_edid:
                edid_header = line_split[0][:16]

                if edid_header != "00ffffffffffff00":
                    raise GenericError("EDID for {} corrupted".format(connection_name))

                # This will break if edid format changes at all, but there really isn't a
                # better way of doing this unfortunately.
                monitor_id = line_split[0][16:20]

                dimensions_split = monitor_dimensions.find('+')
                size = monitor_dimensions[:dimensions_split]
                offset = monitor_dimensions[dimensions_split + 1:]
                size_split = size.split('x')
                offset_split = offset.split('+')

                monitor = Monitor(connection_name, monitor_id, int(size_split[0]),
                                  int(size_split[1]), int(offset_split[0]), int(offset_split[1]))
                self.monitors[connection_name] = monitor

                waiting_edid = False

    def __str__(self):
        s = ""
        for (k, v) in self.monitors.items():
            s += "Monitor - " + v.__str__() + "\n"
        return s

