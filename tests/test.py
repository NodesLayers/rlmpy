import os
import sys
from pprint import pprint

# add rlmpy to python path
lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print(lib_path)
sys.path.append(lib_path)

import rlmpy


def test2():
    import re

    regex = r"^[A-Za-z0-9_]+ v[0-9]+: [A-Za-z0-9]+@[a-zA-Z0-9]+"

    test_str = "sapphire_ae_ofx_sparks_102f v20190925: ashwinip@dawson2 1/0 at 03/07 14:10  (handle: b5)"
    match = re.findall(regex, test_str)
    print(match)
    return

    matches = re.finditer(regex, test_str, re.MULTILINE)

    for matchNum, match in enumerate(matches, start=1):

        print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
                                                                            end=match.end(), match=match.group()))

        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1

            print("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum,
                                                                            start=match.start(groupNum),
                                                                            end=match.end(groupNum),
                                                                            group=match.group(groupNum)))


def test1():
    # server_data = rlmpy.rlmInfo(server="license.lola.lola-post.com", port="4101")
    server_data = rlmpy.rlmInfo(server="license.lola.lola-post.com", port="5053", rlmutil_exe="S:/Github/StudioApi/bin/rlm/rlmutil.exe")
    #pprint(server_data)
    #print(dir(server_data))

    # pprint(server_data.raw_data)
    print("==========================")
    pprint(server_data.licenses)
    print("==========================")
    print("Available:")
    pprint(server_data.counts)
    print("Reserved:")
    pprint(server_data.reserved)
    print("==========================")
    # pprint(server_data.handles)


    #extract_license_data_from_rlmutil_output(get_licenses(None, port_at_server="4101@license.lola.lola-post.com", all=True))


if __name__ == "__main__":
    test1()