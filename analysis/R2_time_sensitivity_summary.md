# Time-dimension sensitivity (revision R2) — summary

Guards: Shapley audit (8 corners x 13 pathways, and both ends) reproduced, worst deviation 4.87e-05 t-CO2/y; waste-only storage break-even 4,416.7 t-CO2/y fossil (published 4,417); four published endpoints reproduced, worst relative CRF deviation 3.8e-07, all ranks equal.

## A. Linear background trajectory 2025 -> 2050 (all three drivers together)

| year | grid | fossil CO2 | S0 | G1 | G1-S0 | G2-S0 | U2a | rank order (best first) |
|---|---|---|---|---|---|---|---|---|
| 2025 | 0.423 | 26,475 | 18,737 | 6,938 | -11,799 | -11,742 | -45,803 | U2a U2b R1 R2 R3 G1 G2 S0 U1 M1 M2 M3 M4 |
| 2030 | 0.352 | 23,263 | 16,856 | 6,101 | -10,755 | -10,710 | -50,941 | U2a U2b R1 R2 R3 G1 G2 U1 S0 M1 M2 M3 M4 |
| 2035 | 0.282 | 20,052 | 14,975 | 5,381 | -9,593 | -9,559 | -55,579 | U2a U2b R1 R2 R3 G1 G2 U1 S0 M1 M2 M3 M4 |
| 2040 | 0.211 | 16,840 | 13,093 | 4,780 | -8,313 | -8,288 | -59,716 | U2a U2b R1 R2 R3 U1 G1 G2 S0 M1 M2 M3 M4 |
| 2045 | 0.141 | 13,628 | 11,212 | 4,297 | -6,915 | -6,900 | -63,353 | U2a U2b U1 R1 R2 R3 G1 G2 S0 M1 M2 M3 M4 |
| 2050 | 0.070 | 10,416 | 9,331 | 3,932 | -5,399 | -5,392 | -66,489 | U2a U2b U1 R1 R2 R3 G1 G2 S0 M1 M2 M3 M4 |

Leader in every year: ['U2a']; storage minus reference ranges -11,799 to -5,399 (G1), -11,742 to -5,392 (G2); negative in every year: True.
Pathways whose rank changes somewhere along the path: ['G1', 'G2', 'R1', 'R2', 'R3', 'S0', 'U1'].
  G1: 2025: 6, 2036: 7
  G2: 2025: 7, 2036: 8
  R1: 2025: 3, 2045: 4
  R2: 2025: 3, 2045: 4
  R3: 2025: 5, 2045: 6
  S0: 2025: 8, 2028: 9
  U1: 2025: 9, 2028: 8, 2036: 6, 2045: 3

## B. Path-free sweep: grid 0.423 -> 0.07 t-CO2/MWh x waste fossil carbon 26,475 -> 10,416 t-CO2/y

- hydrogen at its 2025 value: G1-S0 from -19,024 to 351, G2-S0 from -19,015 to 396; storage below the reference everywhere: False; leader everywhere: ['U2a'] (smallest margin over second 33,041 t-CO2/y)
- hydrogen at its 2050 value: G1-S0 from -19,024 to 351, G2-S0 from -19,015 to 396; storage below the reference everywhere: False; leader everywhere: ['U2a'] (smallest margin over second 33,041 t-CO2/y)

Break-even fossil combustion CO2 of storage (G1 = S0; total waste carbon at its 2050 value) against the grid factor:
  grid 0.070: 4,417 t-CO2/y fossil (plastic ~2.1 % wet, linear rule 5 % at 10,416)
  grid 0.150: 5,865 t-CO2/y fossil (plastic ~2.8 % wet, linear rule 5 % at 10,416)
  grid 0.250: 7,675 t-CO2/y fossil (plastic ~3.7 % wet, linear rule 5 % at 10,416)
  grid 0.350: 9,485 t-CO2/y fossil (plastic ~4.6 % wet, linear rule 5 % at 10,416)
  grid 0.423: 10,806 t-CO2/y fossil (plastic ~5.2 % wet, linear rule 5 % at 10,416)

## C. Every annual endpoint 2026 -> 2125

- treatment A: leader at every endpoint ['U2a'], second ['U2b']; U2b share of the U2a benefit 28.1% at 2026, 32.3% at 2030, 73.4% at 2050, 94.3% at 2125; pathways whose rank changes across endpoints: none
- treatment B: leader at every endpoint ['U2a'], second ['U2b']; U2b share of the U2a benefit 28.1% at 2026, 32.3% at 2030, 73.4% at 2050, 94.3% at 2125; pathways whose rank changes across endpoints: ['G1', 'G2', 'R2', 'R3']
    G1: 2026: 5, 2049: 4, 2060: 3
    G2: 2026: 6, 2050: 5, 2060: 4
    R2: 2026: 3, 2030: 4, 2049: 5, 2050: 6
    R3: 2026: 4, 2030: 3, 2060: 5
