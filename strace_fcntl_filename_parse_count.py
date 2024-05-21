import re
import sys


def main():
    file = open(sys.argv[1], "r")

    files_cnt = {}

    line = file.readline()
    while line != '':

        columns = line.split()

        # 2121534 09:02:21.573327 fcntl(35</tmp/krb5cc_981>, F_OFD_SETLKW, {l_type=F_RDLCK, l_whence=SEEK_SET, l_start=0, l_len=0}) = 0 <0.000005>
        if "fcntl" in columns[2]:
            match = re.search('<(.*)>', columns[2])
            if match:
                f = f'{match.group(1)}'
                if f in files_cnt:
                    files_cnt[f] += 1
                else:
                    files_cnt[f] = 1

        line = file.readline()

    for f, cnt in files_cnt.items():
        print(f'{f} : {cnt}')


if __name__ == "__main__":
    main()
