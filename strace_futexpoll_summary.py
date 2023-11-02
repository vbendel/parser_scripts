import sys


def get_pid_from_line(line):
    return line.split()[0]

def get_time_from_line(line):
    time_column = line.split()[-1]
    time_string = time_column[1:-1]
    return time_string

def main():
    file = open(sys.argv[1], "r")

    pid_futex_wait = []
    pid_poll_wait = []
    futex_wait_count = 0
    futex_wait_time = 0
    poll_count = 0
    poll_wait_time = 0

    line = file.readline()
    while line != '':
        try:
            if "detached" in line:
                pass

            elif "FUTEX_WAIT" in line:
                if "unfinished" in line:
                    pid_futex_wait.append(get_pid_from_line(line))
                else:
                    futex_wait_count += 1
                    futex_wait_time += float(get_time_from_line(line))

            elif "poll(" in line:
                if "unfinished" in line:
                    pid_poll_wait.append(get_pid_from_line(line))
                else:
                    poll_count += 1
                    poll_wait_time += float(get_time_from_line(line))

            elif "futex resumed" in line:
                pid = get_pid_from_line(line)
                if pid in pid_futex_wait:
                    pid_futex_wait.remove(pid)
                    futex_wait_count += 1
                    futex_wait_time += float(get_time_from_line(line))

            elif "poll resumed" in line:
                pid = get_pid_from_line(line)
                if pid in pid_poll_wait:
                    pid_poll_wait.remove(pid)
                    poll_count += 1
                    poll_wait_time += float(get_time_from_line(line))
        except ValueError:
            print(f"ERROR: {line}")

        line = file.readline()
    
    if futex_wait_count > 0:
        print("  FUTEX:")
        print("=======================")
        print(f"Total count: {futex_wait_count}")
        print(f"Total time spend witing: {futex_wait_time:.6f}")
        print(f"Average wait time: {futex_wait_time/futex_wait_count:.6f}")
        print("=======================")
    if poll_count > 0:
        print("  POLL:")
        print("=======================")
        print(f"Total count: {poll_count}")
        print(f"Total time spend witing: {poll_wait_time:.6f}")
        print(f"Average wait time: {poll_wait_time/poll_count:.6f}")
        print("=======================")


if __name__ == "__main__":
    main()