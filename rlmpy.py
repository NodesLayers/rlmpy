import os
import platform
from pprint import pprint
import subprocess
from subprocess import PIPE
import re

REGEX_HANDLE = r"^[A-Za-z0-9_]+ v[0-9.]+: [A-Za-z0-9]+@[a-zA-Z0-9]+"
REGEX_LICENSE = r"^[A-Za-z0-9_]+ v[0-9.]+, pool: [0-9]+"
REGEX_LICENSE2 = r"^[A-Za-z0-9_]+: [0-9.]+, # reservations: [0-9]+, inuse: [0-9]+, exp: [a-zA-Z0-9]+"
REGEX_LICENSE3 = r"^[A-Za-z0-9_]+: [0-9]+, min_remove: [0-9_]+, total checkouts: [0-9]+"


class rlmInfo():
    def __init__(self, server=None, port=None, product=None, isv=None, users=None, rlmutil_exe=None):
        """Connects to the RLM server, gets the output from rlmutil and parses it into various dictionaries use"""

        # rlmutril exe to use
        if not rlmutil_exe:
            print("Error: no rlmutil exectuble specified!")
        else:
            self.rlmutil_exe = rlmutil_exe

        # server
        self.server = server
        if not server:
            print("Error: no server specified!")

        # port
        self.port = port
        if not port:
            print("Error: no port specified!")

        # handles
        self.raw_handles = None
        self.handles = None
        self.handles_by_product = None

        #
        self.reserved = None
        self.available = None
        self.counts = None
        self.raw_data = None
        self.licenses = None

        self.product = product
        self.isv = isv
        self.users = users

        # get data
        self.get_data()

        # parse all data and extract info
        self.parse_rlm_data()

    def refresh_data(self):
        self.get_data()

    def parse_rlm_data(self):
        """ Extracts the License data from the rlmutil -a command output """
        output = self.raw_data

        # Parse license data from output
        handles = []
        license_data_list = []
        item = []
        for line in output.split("\n"):
            line = line.strip()
            # print(line)

            if re.findall(REGEX_LICENSE, line):
                item.append(line)
            if "UNCOUNTED" in line:
                item.append(line)
                item.append(None)
                license_data_list.append(item)
                # reset the item for the for loop
                item = []
                continue
            if re.findall(REGEX_LICENSE2, line):
                item.append(line)
            if re.findall(REGEX_LICENSE3, line):
                item.append(line)
                license_data_list.append(item)
                # reset the item for the for loop
                item = []
            if re.findall(REGEX_HANDLE, line):
                handles.append(line)

        # parse the data_list items to find license data
        licenses = []
        counts = {}
        reserved_amount = {}
        for item in license_data_list:
            # print(item[1])
            # first line data
            # hieroplayer_i v2022.1107, pool: 3
            license = item[0].split(" ")[0].strip()
            version = item[0].split(" ")[1].strip(",").strip()
            pool = item[0].split(" ")[2].strip()

            # second line data
            # count: 15,  # reservations: 0, inuse: 0, exp: 7-nov-2022
            if "UNCOUNTED" in item[1]:
                inuse = int(item[1].split("inuse: ")[-1])
                count = 0
                reserved = 0
                exp = None
            else:
                count = int(item[1].split(" ")[1].strip(","))
                reserved = int(item[1].split("reservations:")[1].split(",")[0].strip())
                inuse = int(item[1].split("inuse:")[1].split(",")[0].strip())
                exp = item[1].split("exp:")[1].strip()

            if item[2]:
                # third line data
                # obsolete: 0, min_remove: 120, total checkouts: 3
                obsolete = int(item[2].split("obsolete:")[1].split(",")[0].strip())
                min_remove = int(item[2].split("min_remove:")[1].split(",")[0].strip())
                total_checkouts = int(item[2].split("total checkouts:")[1].strip())
            else:
                obsolete = 0
                min_remove = 0
                total_checkouts = 0

            data = {
                "license": license,
                "version": version,
                "pool": pool,
                "count": count,
                "reserved": reserved,
                "inuse": inuse,
                "exp": exp,
                "obsolete": obsolete,
                "min_remove": min_remove,
                "total_checkouts": total_checkouts
            }

            if license in counts.keys():
                counts[license] += count
            else:
                counts[license] = count
            if license in reserved_amount.keys():
                reserved_amount[license] += reserved
            else:
                reserved_amount[license] = reserved
            licenses.append(data)

            # update class info
            self.licenses = licenses
            self.counts = counts
            self.available = counts
            self.reserved = reserved_amount

            # save the raw handles and refresh the handle list and per license dict
            self.raw_handles = handles
            self.refresh_handles()

    def refresh_handles(self):
        """Uses self.raw_handles to parse the handles as a list and a as a dict per license"""
        # output a dictionary per license in use
        filtered_handles = []
        for handle in self.raw_handles:
            handle = re.split(r"[0-9]{1}/[0-9]{1} ", handle)[0]

            # user_at_machine = re.findall(handle_user_at_machine_regex, handle)[0]
            # data = {
            #     "product": handle.split(" ")[0],
            #     "user": user_at_machine.split("@")[0],
            #     "machine": user_at_machine.split("@")[1],
            # }
            if handle not in filtered_handles:
                filtered_handles.append(handle)

        filtered_handles.sort()
        self.handles = filtered_handles

        products = []
        handles_by_product = {}
        for handle in filtered_handles:
            product = handle.split(" ")[0]
            user = handle.split(":")[-1].split("@")[0].strip()
            machine = handle.split(":")[-1].split("@")[1].strip()
            if product not in products:
                handles_by_product[product] = {"users": [user], "machines": [machine],
                                               "user@machine": ["{}@{}".format(user, machine)]}
                products.append(product)
            else:
                # update users list
                handles_by_product[product]["users"].append(user)
                handles_by_product[product]["machines"].append(machine)
                handles_by_product[product]["user@machine"].append("{}@{}".format(user, machine))

        self.handles_by_product = handles_by_product

    def get_data(self):
        """
        Gets the raw output from rlmutil
        .\rlmutil.exe rlmstat - c 4101 @ license.acme.com - i foundry - p nukex_i - a
        """

        base_args = [self.rlmutil_exe, "rlmstat", "-c", "{}@{}".format(self.port, self.server)]
        command_args = base_args
        command_args.append("-a")

        #
        # if all:
        #     command_args.append("-a")
        # else:
        #     if self.isv:
        #         command_args.append("-i")
        #         command_args.append(self.isv)
        #
        #     if self.product:
        #         command_args.append("-p")
        #         command_args.append(self.product)
        #
        # if self.users:
        #     command_args = base_args
        #     command_args.append("-u")

        print("Command line:")
        print(" ".join(command_args))

        # run process
        proc = subprocess.Popen(command_args, stdout=PIPE, shell=True)
        output = proc.stdout.read().decode("utf-8")

        self.raw_data = output