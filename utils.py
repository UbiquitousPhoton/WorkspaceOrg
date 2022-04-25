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

from subprocess import Popen, PIPE
from shlex import split

def do_shell_exec(exec_string, expected_result = 0):

    """
    Helper function to do shell executions
    """

    shell_process = Popen(split(exec_string), stdin=PIPE, stdout=PIPE, stderr=PIPE)

    (shell_stdout, shell_stderr) = shell_process.communicate()

    if shell_process.returncode != expected_result:
        self.logger_manager.log(Loglevel.INFO,
                                "{} returned {}".format(exec_string,
                                                        shell_process.returncode))
        logger_manager.log(Loglevel.INFO,
                           "stderr: {}".format(shell_stderr.decode("UTF-8")))
        return False, shell_stdout.decode("utf-8")

    else:
        return True, shell_stdout.decode("utf-8")

