#!/usr/bin/env python3

import pprint

from osmo import Osmo

# This script is a user interface with the following capabilities:
# - monitor the health of the osmo processes
# - get an overview of all connected UEs
# - change values assigned to the UEs (IMSI, IMEI, MSISDN, IP addresses)
# - get an overview of all underlivered SMS messages
# - send SMS messages to UEs
# - call UEs with custom audio files, maybe even reading from microphone?


def renderStatus(data):
    # There are 5 fields: name, count, status, expected and cmd
    # We want to render the data in a table with the following columns:
    # Name, Count, Status, Expected, Command
    # We also want to color the status field:
    # - red if status is not "running", expected is False or count is not 1
    # - otherwise green

    # if the status is red, print the commandline under the row

    names = sorted(data.keys())
    maxname = max([len(name) for name in names])

    print(f"{'Name':>{maxname}} {'Count':>5} {'Status':>10} {'Expected':>10}")

    for name, p in data.items():
        showred = False
        if p["status"] != "running" or not p["expected"] or p["count"] != 1:
            showred = True

        expected = "yes" if p["expected"] else "no"

        if showred:
            print(f"\033[91m", end="")
        else:
            print(f"\033[92m", end="")

        print(f"{name:>{maxname}} {p['count']:>5} {p['status']:>10} {expected:>10}")
        if p["status"] != "running" or not p["expected"] or p["count"] != 1:
            print(f"  {p['cmd']}")

        print(f"\033[0m", end="")


if __name__ == "__main__":
    import os
    import sys
    import time

    thisdir = sys.path[0]
    dockercomposedir = os.path.join(thisdir, "..")
    o = Osmo(dockercomposedir=dockercomposedir)
    while True:
        data = o.getStatus()
        # clear screen
        os.system("clear")
        renderStatus(data)
        time.sleep(1)
