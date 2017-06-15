#!/usr/bin/env python
""" Purpose of this module is to manage user preferences

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017 Ken Farmer
"""
import appdirs

def main():
    user_data_dir = appdirs.user_data_dir('datagristle')
    print(user_data_dir)


if __name__ == '__main__':
   main()
