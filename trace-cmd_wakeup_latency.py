import sys


# pid_stat {
#   "pid": {
#       "state": <ENUM> {"S" | "W" | "R" | "D"}
#       "comm": <STRING>
#       "wakeups": {
#           "time": <FLOAT>
#           "cnt": <INT>
#           "max": <FLOAT>
#           "max_ts": <FLOAT>
#       }
#       "last_wakeup_ts": <FLOAT>
#   }
# }
pid_stat = {}


def get_pid(pid, comm):
    # global pid_stat
    if pid not in pid_stat:
        pid_stat[pid] = {}
        pid_stat[pid]["comm"] = comm
        pid_stat[pid]["state"] = "S"
        pid_stat[pid]["wakeups"] = {"time": 0, "cnt": 0, "max": 0, "max_ts": 0}
        pid_stat[pid]["runtime"] = {"accounted": 0, "real": 0}
        pid_stat[pid]["last_wakeup_ts"] = 0
        pid_stat[pid]["last_schedule_ts"] = 0

    return pid_stat[pid]


def print_result():
    print("       PID   COMM   Wakeup lat.   SUM    CNT        AVG        MAX")
    for pid, stats in pid_stat.items():
        if "swapper" in stats["comm"]:
            continue

        try:
            avg = stats["wakeups"]["time"] / stats["wakeups"]["cnt"]
        except ZeroDivisionError:
            avg = 0

        print(f"{pid: >10}  " +
              f"{stats["comm"]: <15}"
              f"{stats["wakeups"]["time"]:>10.6f} " +
              f"{stats["wakeups"]["cnt"]: >6} " +
              f"{avg:>10.6f} " +
              f"{stats["wakeups"]["max"]:>10.6f} " +
              f" @ {stats["wakeups"]["max_ts"]:.6f}")


def main():
    file = open(sys.argv[1], "r")

    line = file.readline()

    while line != "":

        # print(f'DEBUG: Processing line: "{line}"')

        columns = line.split()

        if len(columns) < 3:
            line = file.readline()
            continue

        #           <idle>-0     [010] 1713251161.254725: sched_waking:         comm=trace-cmd pid=25847 prio=120 target_cpu=011
        if "sched_waking" in columns[3]:

            pid = columns[5].split('=')[1]
            comm = columns[4].split('=')[1]
            wake_time = float(columns[2][:-1])

            stats = get_pid(pid, comm)

            if stats["state"] == "S" or stats["state"] == "D":
                stats["state"] = "W"
                stats["wakeups"]["cnt"] += 1
                stats["last_wakeup_ts"] = wake_time

        #          <idle>-0     [009] 1713251161.254727: sched_switch:         swapper/9:0 [120] S ==> trace-cmd:25851 [120]
        elif "sched_switch" in columns[3]:

            tmp = columns[4].split(":")
            pid_from = tmp[1]
            comm_from = tmp[0]
            state_from = columns[6]

            tmp = columns[8].split(":")
            pid_to = tmp[1]
            comm_to = tmp[0]
            # print(f'DEBUG: PIDs from={pid_from} to={pid_to} in "{line}"')

            sched_time = float(columns[2][:-1])

            stats_from = get_pid(pid_from, comm_from)
            stats_to = get_pid(pid_to, comm_to)

            if stats_from["state"] == "R":
                stats_from["state"] = state_from

            if stats_to["state"] == "W" or stats_to["state"] == "D":
                latency = sched_time - stats_to["last_wakeup_ts"]
                stats_to["wakeups"]["time"] += latency
                stats_to["last_wakeup_ts"] = 0
                if stats_to["wakeups"]["max"] < latency:
                    stats_to["wakeups"]["max"] = latency
                    stats_to["wakeups"]["max_ts"] = sched_time

            stats_to["state"] = "R"

        line = file.readline()

    print_result()


if __name__ == "__main__":
    main()
