#!/usr/bin/env python

import sys
import fileinput
import collections


def main():
   
    alphas = list('abcdefghigjlmnopqrstuvwxyz')
    freq   = collections.defaultdict(int)

    for rec in fileinput.input():
        for character in list(rec.lower()):
            freq[character] += 1

    print freq 
    for alpha in alphas:
        count = freq[alpha]
        print '%(alpha)s - %(count)d' % locals()



if __name__ == '__main__':
   main()
