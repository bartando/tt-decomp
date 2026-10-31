"""Boundary model for the existing double-precision CRT remainder.

Its stock symbol-map range stops at 0x82431EA0, inside its loop (the real tail
returns at 0x82431EF8). Model only that library boundary using IEEE fmod rather
than silently stubbing the truncated tail. The three lifted routines themselves
execute original PPC, with every nested call and result compared.
"""
import math
from liftcheck.spec import *


def remainder(c):
    value, period = c.f(1), c.f(2)
    try:
        result = math.fmod(value, period)
    except ValueError:
        result = float('nan')
    c.ret(f1=result)


CALLS = {0x82431D78: model(remainder, args=('f1', 'f2'))}
