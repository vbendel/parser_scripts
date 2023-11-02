
import re
import sys
from strace_timestamp_class import Timestamp

futex_waiters = {}
pid_waiters = {}
futex_last_wake = {}
futex_holders = {}
pid_holders = {}
pid_last_action = {}

def futex_wait_timeout(pid):
    global futex_waiters
    global pid_waiters

    #print(f"DEBUG: Calling futex_wait_timeout({pid})")

    pid_wait_data = pid_waiters.pop(pid)
    futex_addr = pid_wait_data[0]
    futex_waiters[futex_addr].pop(pid)


def futex_take(futex_addr, pid, ts):
    futex_wait(futex_addr, pid, ts)
    futex_wait_finish(pid, ts)


def futex_wait_finish(pid, ts):
    global futex_waiters
    global pid_waiters
    global pid_holders
    global futex_last_wake

    #print(f"DEBUG: calling futex_wait_finish({pid}, {ts}))")

    if pid not in pid_waiters:
        print("DEBUG: WARNING: futex_wait_finish returned prior " +
              f"to futex WAIT call - pid={pid} ts={ts}")
        return
    
    pid_wait_data = pid_waiters.pop(pid)
    futex_addr = pid_wait_data[0]
    wait_start_ts = pid_wait_data[1]
    
    if futex_addr not in futex_waiters:
        raise Exception(
            "ERROR: futex_wait_finish doesn't see reference for futex_addr")
    
    waiters = futex_waiters[futex_addr]
    waiters.pop(pid)

    if pid not in pid_holders:
        pid_holders[pid] = {futex_addr: ts}
    else:
        pid_holders[pid][futex_addr] = ts

    futex_holders[futex_addr] = (pid, ts)

    print(f"Futex {futex_addr} now held by PID={pid}, " +
          f"wait_time={ts-wait_start_ts}, " +
          f"has {len(futex_waiters[futex_addr])} other waiters")
    if len(waiters) > 0:
        print("          PID : WAIT_START      [delta]")
        for p in waiters:
            print(f"   {p:10d} : {waiters[p]} [{ts-waiters[p]}]")
        print("======================================================")
    if futex_addr in futex_last_wake:
        print(f"    Associated futex_wake was called {ts-futex_last_wake[futex_addr]} ago.")
    

        
def futex_wait(futex_addr, pid, ts):
    global futex_waiters
    global pid_waiters
    global futex_holders
    
    #print(f"DEBUG: calling futex_wait({futex_addr}, {pid}, {ts}))")

    if futex_addr not in futex_waiters:
        futex_waiters[futex_addr] = {pid: ts}
    else:
        futex_waiters[futex_addr][pid] = ts

    pid_waiters[pid] = (futex_addr, ts)

    print(f"Futex {futex_addr} has new waiter PID={pid}, plus {len(futex_waiters[futex_addr])} other waiters")

    if futex_addr in futex_holders:
        holder_data = futex_holders[futex_addr]
        print(f"    Current holder PID={holder_data[0]} for {ts-holder_data[1]}")
    

def futex_wake(futex_addr, pid, ts):
    global futex_waiters
    global futex_last_wake
    global pid_holders

    #print(f"DEBUG: calling futex_wake({futex_addr}, {pid}, {ts}))")
    
    if futex_addr not in futex_waiters:
        futex_waiters[futex_addr] = {}

    if pid not in pid_holders:
        pid_holders[pid] = {}
    else:
        if futex_addr in pid_holders[pid]:
            pid_holders[pid].pop(futex_addr)
    
    futex_last_wake[futex_addr] = ts

    print(f"Futex {futex_addr} waking by PID={pid}.")

    held_futexes = pid_holders[pid]
    if len(held_futexes) > 0:
        print("    Still holds futexes: ")
        print("                 futex : aquire time")
        for f in held_futexes:
            print(f"        {f} : {held_futexes[f]}")

    

def main():
    file = open(sys.argv[1], "r")

    global pid_last_action

    line = file.readline()
    while line != '':

        #print(line)

        # 2287359 13:40:45.993313 futex(0x946054c, FUTEX_WAIT_PRIVATE, 0, NULL <unfinished ...>
        # 2287356 13:40:45.993395 futex(0x8ad796c, FUTEX_WAIT_PRIVATE, 0, NULL <unfinished ...>
        # 2287357 13:41:08.599538 futex(0x9a3c78c, FUTEX_WAKE_PRIVATE, 1 <unfinished ...>
        # 1442908 13:41:08.599937 futex(0x8ad7010, FUTEX_WAKE_PRIVATE, 1) = 0 <0.000011>

        match = re.search('^(\d+) ([0-9:.]+) futex\(([x0-9abcdef]+), (FUTEX\w+), (.*)', line)  # g1=PID g2=TS g3=futex_addr g4=futex_op g5=rest
        if match:
            pid = int(match.group(1))
            ts = Timestamp(match.group(2))
            futex_addr = match.group(3)
            futex_op = match.group(4)
            rest = match.group(5)

            #print(f"DEBUG: Got: PID={pid} TS={ts} futex_addr={futex_addr} futex_op={futex_op} rest=\"{rest}\"")

            if "FUTEX_WAKE" in futex_op:
                pid_last_action[pid] = futex_op
                futex_wake(futex_addr, pid, ts)

            elif "FUTEX_WAIT" in futex_op:
                pid_last_action[pid] = futex_op
                if "= 0" in rest:
                    futex_take(futex_addr, pid, ts)

                if "= -1" not in rest and "unfinished" not in rest and "detached" not in rest:
                    print(f"ERROR: bogus FUTEX_WAIT retval on line: \"{line}\" with parsed rest: \"{rest}\"")
                futex_wait(futex_addr, pid, ts)

            else:
                print(f"DEBUG: Unknown futex op: {futex_op} on line: {line}")

        
        # 4032167 13:41:38.646898 <... futex resumed>) = 0 <52.654002>
        # 4032167 13:41:38.647183 <... futex resumed>) = 1 <0.000118>
        # 4148144 13:41:38.649018 <... futex resumed>) = 0 <52.656150>
        # 2299809 13:41:38.649729 <... futex resumed>) = -1 EAGAIN (Resource temporarily unavailable) <0.000431>
        # 1442908 13:41:38.650023 <... futex resumed>) = ? ERESTARTSYS (To be restarted if SA_RESTART is set) <0.001028>

        match = re.search('^(\d+) ([0-9:.]+) <... futex resumed>\) = (.+) .*$', line)  # g1=PID g2=TS g3=retval
        if match:
            pid = int(match.group(1))
            ts = Timestamp(match.group(2))
            retval = match.group(3)

            if pid in pid_last_action:
                if "FUTEX_WAIT" in pid_last_action[pid]:
                    if retval == "0":
                        futex_wait_finish(pid, ts)
                    else:
                        futex_wait_timeout(pid)
            
        # match = re.search('([a-z0-9]*)-([0-9]*) .* kmalloc.* \((.*)\) .* ptr=0x([0-9abcdef]*) .* bytes_alloc=([0-9]*)', line)
        # if match:
        #     comm = match.group(1)
        #     pid = int(match.group(2))
        #     func = match.group(3)
        #     ptr = match.group(4)
        #     size = int(match.group(5))
        #
        #     print('{} - {} .. {} .. {}  = {}'.format(comm,pid,func,ptr,size))
# if match:
#     substr = int(match.group(1))

        # global futex_waiters
        # global futex_holders
        # global futex_last_wake
        # global pid_waiters
        # global pid_holders
        # print(f"futex_waiters: {futex_waiters}")
        # print(f"futex_holders: {futex_holders}")
        # print(f"futex_last_wake: {futex_last_wake}")
        # print(f"pid_waiters: {pid_waiters}")
        # print(f"pid_holders: {pid_holders}")

        line = file.readline()


if __name__ == "__main__":
    main()
