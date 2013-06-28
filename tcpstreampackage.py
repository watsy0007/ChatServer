# -*- coding:utf-8 -*-
__author__ = 'watsy'

import json
from protocol import Protocol


class TCPStreamPackage(object):

    def __init__(self , callback):
        super(TCPStreamPackage , self).__init__()

        self.datas = ''
        self._package_decode_callback = callback

    def add(self, data):
        #组包
        if len(self.datas) == 0:
            self.datas = data
        else:
            self.datas = "%s%s" % (self.datas , data)

        #拆包
        length = -1
        length_index = self.datas.find('length\" :')
        if length_index != -1:
            length_end = self.datas.find(',' , length_index + 9 , length_index + 9 + 10)
            if length_end == -1:
                length_end = self.datas.find('}', length_index + 9 , length_index + 9 + 10)

            if length_end != -1:
                length = self.datas[length_index + 9 :length_end]

        if length != -1:
            length = int(length.strip())

        if length != -1 and length <= len(self.datas):
           package = self.datas[0:length]
           package = Protocol.checkPackage(package)

           if self._package_decode_callback:
               self._package_decode_callback(package)

           if len(self.datas) == length:
                self.datas = ''
           else:
                self.datas = self.datas[length]


