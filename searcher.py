#! /usr/bin/env python3

import re
import sys

read_from = open('/home/huhu/Desktop/proj/pycharm/mdxtxt_parser/lexi.txt', 'r', encoding='utf-8')

tt = read_from.read()
read_from.close()

if __name__ == '__main__':
    word = sys.argv[1]
    search_res = re.search(f'^{word}\\n[\\w\\W]*?\\n\\w', tt, re.M)
    if search_res is None:
        print("No result")
    else:
        print(search_res.group(0)[:-1])
