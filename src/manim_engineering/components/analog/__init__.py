"""Analog component stubs (symbol-only, Scope A).

See ``docs/ROADMAP.md`` for the continuous-physics roadmap (Scope B/C).
"""

from manim_engineering.components.analog.bjt import NPN, PNP
from manim_engineering.components.analog.diode import Diode
from manim_engineering.components.analog.nmos import NMOS
from manim_engineering.components.analog.nmos_depletion import NMOSDepletion
from manim_engineering.components.analog.op_amp import OpAmp
from manim_engineering.components.analog.pmos import PMOS
from manim_engineering.components.analog.pmos_depletion import PMOSDepletion
from manim_engineering.components.analog.zener import ZenerDiode

__all__ = [
    "Diode",
    "NMOS",
    "NMOSDepletion",
    "NPN",
    "OpAmp",
    "PMOS",
    "PMOSDepletion",
    "PNP",
    "ZenerDiode",
]
