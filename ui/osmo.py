#!/usr/bin/env python3

import re
import subprocess


class Osmo:
    def __init__(self, dockercomposedir: str = None):
        self.dockercomposedir = dockercomposedir
        pass

    def _read_status(self) -> list:
        # get the status of all osmo processes

        # The docker-compose file is 1 directory up from here, use it to
        # execute docker compose top osmo.
        # The result is a space-separated table with the second line being the header
        # and the rest being the data.
        # We want to parse the entire data table into a list of dictionaries.

        dpsout = subprocess.run(
            ["docker", "compose", "top", "osmo"],
            cwd=self.dockercomposedir,
            capture_output=True,
            text=True,
        )
        if dpsout.returncode != 0:
            raise Exception("Error: failed to execute docker compose top osmo")

        # split the output into lines
        lines = dpsout.stdout.split("\n")

        # split the second line into column names, assuming it contains the column names
        assert len(lines) >= 2, "Error: docker compose top osmo output is too short"
        assert "CMD" in lines[1], "Error: docker compose top osmo output does not contain column name 'CMD'"

        # for each of the column names, record the name as well as the index of its first character, and its width
        # for the last column, the width is None to indicate that it goes to the end of the line
        # We use regex to split the columns
        columns = []
        currentname = ""
        startcolumn = 0
        header = lines[1]

        while header != "":
            # extract the next column name with any trailing spaces
            m = re.match(r"(\S+)(\s*)", header)
            if m is None:
                break
            currentname = m.group(1)
            header = header[m.end(0) :]
            if header == "":
                width = None
            else:
                width = m.end(0)
            colinfo = (currentname, startcolumn, width)
            columns.append(colinfo)

            if width is not None:
                startcolumn += width

        # for each of the data lines, extract the data into a dictionary
        data = []
        for line in lines[2:]:
            if line == "":
                break
            row = {}
            for i, (name, startcolumn, width) in enumerate(columns):
                if width is None:
                    row[name] = line[startcolumn:]
                else:
                    row[name] = line[startcolumn : startcolumn + width]
                row[name] = row[name].strip()
            data.append(row)

        return data

    def getStatus(self) -> dict:
        # update the global state with the status of all osmo processes

        expected_processes = {
            "entrypoint": "bash /configs/entrypoint.sh",
            "osmo-bsc": "osmo-bsc -c /etc/osmocom/osmo-bsc.cfg",
            "osmo-msc": "osmo-msc -c /etc/osmocom/osmo-msc.cfg",
            "osmo-hlr": "osmo-hlr -c /etc/osmocom/osmo-hlr.cfg",
            "osmo-mgw": "osmo-mgw -c /etc/osmocom/osmo-mgw.cfg",
            "osmo-stp": "osmo-stp -c /etc/osmocom/osmo-stp.cfg",
            "osmo-sgsn": "osmo-sgsn -c /etc/osmocom/osmo-sgsn.cfg",
            "osmo-ggsn": "osmo-ggsn -c /etc/osmocom/osmo-ggsn.cfg",
            "osmo-pcu": "osmo-pcu -c /etc/osmocom/osmo-pcu.cfg",
            "osmo-cbc": "osmo-cbc -c /etc/osmocom/osmo-cbc.cfg",
            "osmo-sip-connector": "osmo-sip-connector -c /etc/osmocom/osmo-sip-connector.cfg",
            "asterisk": "asterisk",
            "osmo-trx-lms": "osmo-trx-lms -C /etc/osmocom/osmo-trx-lms.cfg",
            "osmo-bts-trx": "osmo-bts-trx -c /etc/osmocom/osmo-bts.cfg",
            "dnsmasq (sgsn)": "dnsmasq -C /configs/dnsmasq/sgsn.conf",
            "dnsmasq (apn0)": "dnsmasq -C /configs/dnsmasq/apn0.conf",
            "sleep": "sleep infinity",
        }

        data = self._read_status()

        healthdata = {}

        # possible states:
        # - running and expected
        # - running and not expected
        # - not running and expected

        # each process should be running exactly once, otherwise we need to show that a second one is running unexpectedly

        # for each of the expected processes, add a default status of "not found" that will be overwritten later
        for name, cmd in expected_processes.items():
            healthdata[name] = {"cmd": cmd, "status": "not found", "expected": True, "count": 0}

        # for each of the actual processes, update the status
        notfoundcounter = 0
        for row in data:
            found = False
            for name, cmd in expected_processes.items():
                if row["CMD"] == cmd:
                    healthdata[name]["status"] = "running"
                    healthdata[name]["count"] += 1
                    found = True

            if not found:
                notfoundcounter += 1
                healthdata[f"???? ({notfoundcounter})"] = {
                    "cmd": row["CMD"],
                    "expected": False,
                    "status": "running",
                    "count": 1,
                }

        return healthdata


if __name__ == "__main__":
    import os
    import pprint
    import sys

    thisdir = sys.path[0]
    dockercomposedir = os.path.join(thisdir, "..")
    o = Osmo(dockercomposedir=dockercomposedir)
    data = o.getStatus()
    pprint.pprint(data)
