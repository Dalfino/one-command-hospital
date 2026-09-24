#!/usr/bin/env python3
"""Fix Makefile recipe indentation: leading 8-space groups -> real tabs.
Continuation lines (previous line ends with backslash) are left alone."""
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
prev_cont = False
for line in lines:
    stripped = line.rstrip("\n")
    if prev_cont:
        out.append(line)  # keep continuation line as-is
    else:
        fixed = stripped
        while fixed.startswith("        "):
            fixed = "\t" + fixed[8:]
        out.append(fixed + "\n")
    prev_cont = stripped.endswith("\\")

with open(path, "w", encoding="utf-8") as f:
    f.writelines(out)
print(f"fixed {path}")
