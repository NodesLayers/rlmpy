import re
import subprocess
from subprocess import PIPE

REGEX_HANDLE = r"^[A-Za-z0-9_]+ v[0-9.]+: [A-Za-z0-9]+@[a-zA-Z0-9]+"
REGEX_LICENSE = r"^[A-Za-z0-9_]+ v[0-9.]+, pool: [0-9]+"
REGEX_LICENSE2 = r"^[A-Za-z0-9_]+: [0-9.]+, # reservations: [0-9]+, inuse: [0-9]+, exp: [a-zA-Z0-9]+"
REGEX_LICENSE3 = r"^[A-Za-z0-9_]+: [0-9]+, min_remove: [0-9_]+, total checkouts: [0-9]+"


class rlmInfo:
    def __init__(self, server=None, port=None, product=None, isv=None, users=None, rlmutil_exe=None):
        """Connects to the RLM server, gets the output from rlmutil, and parses it into dictionaries."""
        if not rlmutil_exe:
            raise ValueError("No rlmutil executable specified.")
        self.rlmutil_exe = rlmutil_exe

        self.server = server
        if not server:
            raise ValueError("No server specified.")

        self.port = port
        if not port:
            raise ValueError("No port specified.")

        self.raw_handles = None
        self.handles = None
        self.handles_by_product = None

        self.reserved = None
        self.available = None
        self.counts = None
        self.raw_data = None
        self.licenses = None

        self.product = product
        self.isv = isv
        self.users = users

        self.get_data()
        self.parse_rlm_data()

    def get_reserved_count_for_product(self, product):
        """Returns the total number of reserved licenses for the product."""
        reserved = 0
        for license in self.licenses:
            if license["product"] == product:
                reserved += license["reserved"]
        return reserved

    def get_available_count_for_product(self, product):
        """Returns the total number of available licenses for the product."""
        available = 0
        for license in self.licenses:
            if license["product"] == product:
                available += license["available"]
        return available

    def get_inuse_count_for_product(self, product):
        """Returns the total number of licenses currently in use for the product."""
        inuse = 0
        for license in self.licenses:
            if license["product"] == product:
                inuse += license["inuse"]
        return inuse

    def refresh_data(self):
        self.get_data()
        self.parse_rlm_data()

    def parse_rlm_data(self):
        """Extracts license data from the rlmutil -a command output."""
        output = self.raw_data

        handles = []
        license_data_list = []
        item = []
        for line in output.split("\n"):
            line = line.strip()

            if re.findall(REGEX_LICENSE, line):
                item.append(line)
            if "UNCOUNTED" in line:
                item.append(line)
                item.append(None)
                license_data_list.append(item)
                item = []
                continue
            if re.findall(REGEX_LICENSE2, line):
                item.append(line)
            if re.findall(REGEX_LICENSE3, line):
                item.append(line)
                license_data_list.append(item)
                item = []
            if re.findall(REGEX_HANDLE, line):
                handles.append(line)

        licenses = []
        counts = {}
        reserved_amount = {}
        for item in license_data_list:
            if len(item) < 3:
                continue

            license = item[0].split(" ")[0].strip()
            version = item[0].split(" ")[1].strip(",").strip()
            pool = item[0].split(" ")[3].strip()

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

            if item[2] is not None:
                obsolete = int(item[2].split("obsolete:")[1].split(",")[0].strip())
                min_remove = int(item[2].split("min_remove:")[1].split(",")[0].strip())
                total_checkouts = int(item[2].split("total checkouts:")[1].strip())
            else:
                obsolete = 0
                min_remove = 0
                total_checkouts = 0

            data = {
                "license": license,
                "product": license,
                "version": version,
                "pool": pool,
                "count": count,
                "reserved": reserved,
                "inuse": inuse,
                "exp": exp,
                "obsolete": obsolete,
                "min_remove": min_remove,
                "total_checkouts": total_checkouts,
                "available": (count + reserved - inuse),
            }

            licenses.append(data)
            self.licenses = licenses

            if license in counts.keys():
                counts[license] += count
            else:
                counts[license] = count
            if license in reserved_amount.keys():
                reserved_amount[license] += reserved
            else:
                reserved_amount[license] = reserved

            self.counts = counts
            self.available = counts
            self.reserved = reserved_amount
            self.raw_handles = handles
            self.refresh_handles()

    def refresh_handles(self):
        """Uses self.raw_handles to parse the handles as a list and as a dict per license."""
        filtered_handles = []
        for handle in self.raw_handles:
            handle = re.split(r"[0-9]{1}/[0-9]{1} ", handle)[0]
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
                handles_by_product[product] = {
                    "users": [user],
                    "machines": [machine],
                    "user@machine": [f"{user}@{machine}"],
                }
                products.append(product)
            else:
                handles_by_product[product]["users"].append(user)
                handles_by_product[product]["machines"].append(machine)
                handles_by_product[product]["user@machine"].append(f"{user}@{machine}")

        self.handles_by_product = handles_by_product

    def get_data(self):
        """Gets the raw output from rlmutil."""
        command_args = [self.rlmutil_exe, "rlmstat", "-c", f"{self.port}@{self.server}", "-a"]
        proc = subprocess.Popen(command_args, stdout=PIPE, stderr=PIPE)
        stdout, _ = proc.communicate()
        self.raw_data = stdout.decode("utf-8")
