#!/usr/bin/env python3

import sys
import json


def load(p):
    with open(p) as f:
        return json.load(f)


if __name__ == "__main__":
    z = load(sys.argv[1])
    print(z)
