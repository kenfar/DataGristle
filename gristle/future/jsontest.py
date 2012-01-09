#!/usr/bin/env python
""" Purpose of this module is to manage the metadata database

    To do:
       - create classes to access all tables easily through
    Model:

"""

from __future__ import division
import appdirs
import os
import json


#--- CONSTANTS -----------------------------------------------------------
def main():

    data = [ { 'a':'A', 
               'b':(2, 4), 
               'c':3.0 } ]
    data_string = json.dumps(data)
    print 'ENCODED:', data_string

    decoded = json.loads(data_string)
    print 'DECODED:', decoded

    print 'ORIGINAL:', type(data[0]['b'])
    print 'DECODED :', type(decoded[0]['b'])


    encoder = json.JSONEncoder()
    for part in encoder.iterencode(data):
        print 'part: ', part 
    json_string = encoder.encode(data_string)
    print json_string
    


if __name__ == '__main__':
   main()

