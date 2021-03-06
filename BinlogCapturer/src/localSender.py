# Copyright (c) 2020-present ly.com, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import Queue
import threading

class LocalSender(threading.Thread):
    def __init__(self,config):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.config = config
        self.filepath = self.config.get('local','filepath')
        self.queue = Queue.Queue()
        self.condition = threading.Condition()
        self.maxFileSize = 1024 * 1024 * 1024
        if os.path.exists(self.filepath) == False:
            with open(self.filepath, 'w') as f:
                pass

        self.fileSize = os.path.getsize(self.filepath)
        self.outFile = open(self.filepath,'a')
        self.maxTs = 0
        self.checkpoint = 0

    def send(self, sqlItem):
        ts = sqlItem[0]
        self.queue.put(sqlItem)
        self.maxTs = ts
    def getCheckpoint(self):
        return self.checkpoint

    def flush(self):
        self.condition.acquire()
        if self.maxTs != self.checkpoint:
            self.condition.wait()
        self.condition.release()

    def run(self):
        commitTs = 0
        while True:
            self.outFile = open(self.filepath,'a')
            ts = 0
            for i in range(0,1000):
                ts,sql = self.queue.get()
                self.outFile.write(sql + '\n')
                self.fileSize += len(sql)
                if self.queue.empty():
                    break
            self.outFile.close()
            commitTs = ts
            self.condition.acquire()
            self.checkpoint = ts
            if self.checkpoint == self.maxTs:
                self.condition.notify()
            self.condition.release()
        
            if self.fileSize >= self.maxFileSize:
                self.changeFile()
    
    def changeFile(self):
        curTime = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
        bakFileName = self.filepath + '-' + curTime
        os.rename(self.filepath, bakFileName)
        self.fileSize = 0

