# The MIT License (MIT)
#
# Copyright (c) 2015, Nicolas Sebrecht & contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from imapfw import runtime

from ..managers.driver import DriverManager
from ..constants import ARC

import traceback

from ..constants import WRK, DRV


def driverRunner(ui, workerName, driverReceiver, handlerEmitter):
    """The runner for a driver."""

    try:
        ui.debugC(DRV, "starts serving")
        while driverReceiver.serve_next():
            pass
        ui.debugC(DRV, "stopped serving")
        ui.debugC(WRK, "runner ended")

    except Exception as e:
        ui.critical('%s exception occured: %s\n%s',
            workerName, str(e), traceback.format_exc())
        handlerEmitter.interruptionError(e.__class__, str(e))


class DriverArchitectInterface(object):
    def getEmitter(self):   raise NotImplementedError
    def join(self):         raise NotImplementedError
    def kill(self):         raise NotImplementedError
    def start(self):        raise NotImplementedError


class DriverArchitect(DriverArchitectInterface):
    """Architect to seup the driver manager."""
    def __init__(self, workerName):
        self._workerName = workerName

        self.ui = runtime.ui
        self.concurrency = runtime.concurrency
        self._emitter = None
        self._worker = None

        self.ui.debugC(ARC, "{} created", self._workerName)

    def getEmitter(self):
        return self._emitter

    def join(self):
        self._emitter.stopServing()
        self._worker.join()

    def kill(self):
        self._worker.kill()

    def start(self, handlerEmitter):
        self.ui.debugC(ARC, "{} starting driver manager '{}'",
            self.__class__.__name__, self._workerName)

        driverManager = DriverManager(self._workerName)
        receiver, self._emitter = driverManager.split()
        self._worker = self.concurrency.createWorker(
            self._workerName,
            driverRunner, (
                self.ui,
                self._workerName,
                receiver,
                handlerEmitter,
            ))
        self._worker.start()