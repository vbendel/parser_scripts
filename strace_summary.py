import re
import sys

PID_SYSCALL_MAP = {}

# "syscall": 
#       "count":
#       "time":
SYSCALL_STATS = {}


def parse_syscall_name(line):
    match = re.search('(.*)\\(', line)
    if match:
        return f"{match.group(1)}"
    else:
        return None
    

def parse_time_spent(line):
    time_column = line.split()[-1]
    time_string = time_column[1:-1]
    return time_string
    

def account_syscall(syscall, time):
    if syscall == "exit_group" or syscall == "exit":
        return
    try:
        if syscall in SYSCALL_STATS:
            SYSCALL_STATS[syscall]["count"] += 1
            SYSCALL_STATS[syscall]["time"] += float(time)
        elif syscall:
            SYSCALL_STATS[syscall] = {}
            SYSCALL_STATS[syscall]["count"] = 1
            SYSCALL_STATS[syscall]["time"] = float(time)
    except KeyError:
        print(f"ERROR: {syscall} {time} in? {syscall in SYSCALL_STATS}")


def process_line(line):
    columns = line.split(" ")
    if "?" in columns[-1]:
        return
    pid = columns[0]
    syscall = parse_syscall_name(columns[2])
    try:
        if "unfinished" in line:
            PID_SYSCALL_MAP[pid] = syscall
        elif "resumed" in line and pid in PID_SYSCALL_MAP:
            account_syscall(PID_SYSCALL_MAP[pid], parse_time_spent(line))
        elif syscall:
            account_syscall(syscall, parse_time_spent(line))
    except ValueError:
        print(f"ERROR: {line}")
    return


def main():
    file = open(sys.argv[1], "r")

    line = file.readline()
    while line != '':
        process_line(line)
        line = file.readline()

    sorted_syscalls = sorted(SYSCALL_STATS.items(),
                             key=lambda x: x[1]["time"],
                             reverse=True)

    print(f"{'Syscall':>20s} {'Count':>8s} {'Time':>15s} {'Time per call':>15s}")
    for syscall in sorted_syscalls:
        try:
            count = syscall[1]["count"]
            time = syscall[1]["time"]
            print(f"{syscall[0]:>20} {count:>8} {time:>15.6f} {time/count:>15.6f}")
        except KeyError:
            print(syscall)
        except TypeError:
            print(syscall)
            

if __name__ == "__main__":
    main()
