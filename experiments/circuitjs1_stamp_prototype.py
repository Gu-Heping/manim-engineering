"""Isolated stamping prototype inspired by circuitjs1 internals.

This module is intentionally standalone and not imported by runtime paths.
It demonstrates a tiny linear DC solve using a stamp-style API.

Run:
    python experiments/circuitjs1_stamp_prototype.py
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class Stampable:
    def stamp(self, A: np.ndarray, b: np.ndarray) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class Resistor(Stampable):
    n1: int
    n2: int
    ohms: float

    def stamp(self, A: np.ndarray, b: np.ndarray) -> None:
        g = 1.0 / self.ohms
        if self.n1 != 0:
            i = self.n1 - 1
            A[i, i] += g
        if self.n2 != 0:
            j = self.n2 - 1
            A[j, j] += g
        if self.n1 != 0 and self.n2 != 0:
            i = self.n1 - 1
            j = self.n2 - 1
            A[i, j] -= g
            A[j, i] -= g


@dataclass(frozen=True)
class CurrentSource(Stampable):
    n_from: int
    n_to: int
    amps: float

    def stamp(self, A: np.ndarray, b: np.ndarray) -> None:
        # Positive current flows n_from -> n_to.
        if self.n_from != 0:
            b[self.n_from - 1] -= self.amps
        if self.n_to != 0:
            b[self.n_to - 1] += self.amps


def solve_dc(num_nodes_without_gnd: int, elements: list[Stampable]) -> np.ndarray:
    A = np.zeros((num_nodes_without_gnd, num_nodes_without_gnd), dtype=float)
    b = np.zeros(num_nodes_without_gnd, dtype=float)
    for element in elements:
        element.stamp(A, b)
    return np.linalg.solve(A, b)


def main() -> None:
    # Node 0 is ground. Solve node 1 voltage:
    #   1k resistor from node1 to ground, 2mA current source from node1 to ground.
    # KCL => v1/1000 + 0.002 = 0 => v1 = -2V
    elements: list[Stampable] = [
        Resistor(1, 0, 1000.0),
        CurrentSource(1, 0, 0.002),
    ]
    v = solve_dc(num_nodes_without_gnd=1, elements=elements)
    print(f"node1_voltage={v[0]:.6f}V")


if __name__ == "__main__":
    main()
