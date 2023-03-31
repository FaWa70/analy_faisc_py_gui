import numpy as np


def range_str_conv(inp):
    if type(inp) is str:
        print("string input - list output")
        outp = []
        try:
            inp = inp.split(",")
            for idx in range(len(inp)):
                lims = inp[idx].split("-")
                if len(lims) == 1:
                    outp = outp + [int(lims[0])]
                else:
                    outp = outp + list(range(int(lims[0]), int(lims[1]) + 1))
        except ValueError:
            outp = []
    else:
        print("list input - string output")
        inp = np.array(inp).astype(int)
        outp = ""
        first = inp[0]
        last = first
        for idx in range(1, len(inp)):
            if inp[idx] == last + 1:
                last += 1
            else:
                if last > first:
                    outp = outp + str(first) + "-" + str(last) + ", "
                else:
                    outp = outp + str(first) + ", "
                first = inp[idx]
                last = first
        if last > first:
            outp = outp + str(first) + "-" + str(last)
        else:
            outp = outp + str(first)
    return outp

print(range_str_conv(np.array([1, 2, 3, 5, 6, 8, 10])))

print(range_str_conv("1-3, 5-6, 8, 10"))

print(range_str_conv(" "))