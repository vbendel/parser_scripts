from functools import total_ordering

@total_ordering
class Timestamp:

    # TODO: Implement some init verification
    def __init__(self, ts_string):
        tmp = ts_string.split(":")
        self.hour = int(tmp[0])
        self.minute = int(tmp[1])
        tmpsec = tmp[2].split(".")
        self.second = int(tmpsec[0])
        self.subsec = int(tmpsec[1])

    def __str__(self):
        return f"{self.hour:02d}:{self.minute:02d}:{self.second:02d}.{self.subsec:06d}"

    def __add__(self, y):
        of = 0
        subsec = self.subsec + y.subsec
        while subsec >= 1000000:
            of += 1
            subsec -= 1000000

        second = self.second + y.second + of
        of = 0
        while second >= 60:
            of += 1
            second -= 60

        minute = self.minute + y.minute + of
        of = 0
        while minute >= 60:
            of += 1
            minute -= 60

        hour = self.hour + y.hour + of

        return Timestamp(f"{hour}:{minute}:{second}.{subsec}")

    def __sub__(self, y):
        of = 0
        if self.subsec >= y.subsec:
            subsec = self.subsec - y.subsec
        else:
            of = 1
            subsec = 1000000 + self.subsec
            subsec -= y.subsec

        if self.second - of >= y.second:
            second = self.second - y.second - of
            of = 0
        else:
            second = 60 + self.second - of
            second -= y.second
            of = 1

        if self.minute - of >= y.minute:
            minute = self.minute - y.minute - of
            of = 0
        else:
            minute = 60 + self.minute - of
            minute -= y.minute
            of = 1

        if self.hour - of >= y.hour:
            hour = self.hour - y.hour - of
            of = 0
        else:
            #return Timestamp("0:0:0:0") ## TODO: Handle this exception.. somehow :P
            raise Exception("Subtraction into negative.")

        return Timestamp(f"{hour}:{minute}:{second}.{subsec}")
    
    # TODO: Comparison
    def __eq__(self, y):
        if (self.hour == y.hour and
                self.minute == y.minute and
                self.second == y.second and
                self.subsec == y.subsec):
            return True
        else:
            return False

    def __ne__(self, y):
        if (self.hour != y.hour or
                self.minute != y.minute or
                self.second != y.second or
                self.subsec != y.subsec):
            return True
        else:
            return False

    def __lt__(self, y):
        if self.hour == y.hour:
            if self.minute == y.minute:
                if self.second == y.second:
                    if self.subsec == y.subsec:
                        return False
                    else:
                        return self.subsec < y.subsec
                else:
                    return self.second < y.second
            else:
                return self.minute < y.minute
        else:
            return self.hour < y.hour

    def add(self, x):
        self.subsec += x.subsec
        self.second += x.second
        self.minute += x.minute
        self.hour += x.hour

    def us(self):
        us = self.subsec
        us += self.second*1000000
        us += self.minute*60*1000000
        us += self.hour*60*60*1000000
        return us


## Testing:


#ts1 = Timestamp("21:22:33.000100")
#ts2 = Timestamp("22:22:33.000100")

#ts3 = Timestamp("13:20:34.999999")
#ts4 = Timestamp("21:22:33.010100")

#print(ts1)
#print(ts2)
#print(ts4-ts3)


