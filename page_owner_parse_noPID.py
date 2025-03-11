import re
import sys


def get_function_name(bt_line):
    return re.search(r"(\w+)+", bt_line).group(1)


def get_module_name(bt_line):
    match = re.search(r"\[(\w+)\]", bt_line)
    if match:
        return match.group(1)
    else:
        return ""


def count_allocation_backtrace_pairs(filename):
    allocation_data = {}

    with open(filename, "r") as file:
        lines = file.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if it is the start of a record
            if line.startswith("Page allocated via order"):
                allocation_info = line
                order = re.search(r"order (\d+)", allocation_info).group(1)
                backtrace = ""
                j = i + 2

                # Extract the backtrace until an empty line is encountered
                module = ""
                while j < len(lines) and lines[j].strip() != "":
                    try:
                        backtrace += get_function_name(lines[j].strip())
                        module = get_module_name(lines[j].strip())
                    except IndexError:
                        print(f"ERROR: Index error in backtrace parsing on line: {lines[j]}")
                    if module != "":
                        backtrace += f"--[{module}] "
                    else:
                        backtrace += " "
                    j += 1

                # Filter for tuples with backtrace containing a module
                # if module != "":

                # Create the order, and backtrace tuple
                allocation_tuple = (int(order), backtrace)

                # Update the count for the tuple
                if allocation_tuple in allocation_data:
                    data = allocation_data[allocation_tuple]
                    data["count"] += 1
                else:
                    allocation_data[allocation_tuple] = {
                        "count": 1,
                    }

                i = j  # Skip the processed lines
            else:
                i += 1

    return allocation_data


# Check if the filename is provided as a command-line argument
if len(sys.argv) != 2:
    print("Please provide the input file as a command-line argument.")
    sys.exit(1)

filename = sys.argv[1]
alloc_data = count_allocation_backtrace_pairs(filename)

# Print the tuple counts
for allocation_tuple, data in alloc_data.items():
    order, backtrace = allocation_tuple
    count = data["count"]
    result = 2**order * count * 4
    cmd_cnt = {}
    print(
        f"Result: {result} KB : Count: {count} | Order: {order} | {backtrace}"
    )
