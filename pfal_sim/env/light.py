
"""
PFAL Light Module (spinach-first, Kozai-inspired)

This module provides basic photon/power/heat math and a DLI controller.
It's deliberately simple and fast so you can iterate, calibrate, and plug into
the rest of your PFAL sim stack.

Units:
- PPF: μmol s^-1
- PPFD: μmol m^-2 s^-1
- DLI: mol m^-2 d^-1
- Power: W (J s^-1)

Assumptions:
- Nearly all electrical power to LEDs becomes heat in-room (closed PFAL).
- Spectrum is a dict of fractional weights that sum ~1.0.
- Utilization is a simple scalar [0..1] capturing optics, reflectance, canopy LAI.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Sequence
import math


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def ppf_from_dim(dim_frac: float, ppf_max: float, ppe_derate: float = 1.0) -> float:
    """
    Convert dimming fraction to emitted PPF (μmol/s).
    ppe_derate can be used to reduce effective output at high junction temps.
    """
    dim_frac = clamp(dim_frac, 0.0, 1.0)
    return ppf_max * dim_frac * clamp(ppe_derate, 0.0, 1.0)


def electrical_watts(ppf: float, ppe: float, driver_loss: float = 0.04, thermal_derate: float = 0.0) -> Tuple[float, float]:
    """
    Convert emitted PPF (μmol/s) to electrical input power (W), then heat (W).
    - ppe: μmol/J at nominal conditions (effective photon efficacy).
    - driver_loss: AC->DC and driver losses (fraction of input power).
    - thermal_derate: fractional reduction of PPE under high temp; 0.1 => PPE drops 10%.
    Returns: (watts_in, heat_watts)
    """
    eff_ppe = ppe * (1.0 - clamp(thermal_derate, 0.0, 0.9))
    if eff_ppe <= 0:
        raise ValueError("Effective PPE must be > 0")
    # Lamp electrical power before driver loss
    lamp_watts = ppf / eff_ppe
    # Account for driver loss: input power must supply lamp_watts + losses
    watts_in = lamp_watts / (1.0 - clamp(driver_loss, 0.0, 0.5))
    heat_watts = watts_in  # In closed PFAL almost all ends as heat load
    return watts_in, heat_watts


def mix_spectrum(ppf_total: float, spectrum_weights: Dict[str, float]) -> Dict[str, float]:
    """
    Split total PPF into bands per fractional weights.
    spectrum_weights keys can be like: 'B','G','R','FR','UV'.
    """
    s = sum(v for v in spectrum_weights.values())
    if s <= 0:
        raise ValueError("Spectrum weights must sum to > 0")
    return {band: ppf_total * (w / s) for band, w in spectrum_weights.items()}


def utilization_factor(LAI: float, wall_reflectance: float = 0.85, beam_spread_deg: float = 120.0) -> float:
    """
    Very simple utilization model combining optics+reflectance+canopy interception.
    This is a placeholder to be calibrated:
    - Higher wall_reflectance increases utilization.
    - Higher LAI increases absorption (less photon escape).
    - Extremely wide/narrow beams can reduce/utilization slightly.
    Returns scalar in [0.3, 0.98].
    """
    wall_term = 0.55 + 0.45 * clamp(wall_reflectance, 0.0, 0.98)
    lai_term = 1.0 - math.exp(-0.7 * max(LAI, 0.0))  # saturates with LAI
    beam_term = 1.0 - 0.1 * abs(120.0 - clamp(beam_spread_deg, 60.0, 150.0)) / 60.0
    u = wall_term * lai_term * beam_term
    return clamp(u, 0.30, 0.98)


def ppfd_at_canopy(ppf_total: float, utilization: float, lit_area_m2: float) -> float:
    """
    Convert total emitted PPF to canopy PPFD by applying utilization and dividing by area.
    """
    if lit_area_m2 <= 0:
        raise ValueError("Area must be > 0")
    return (ppf_total * clamp(utilization, 0.0, 1.0)) / lit_area_m2


def integrate_dli(ppfd_series: Sequence[float], dt_seconds: float) -> float:
    """
    Numerically integrate DLI from a time series of PPFD (μmol m^-2 s^-1)
    with a constant time step dt_seconds. Returns DLI in mol m^-2 d^-1.
    """
    if dt_seconds <= 0:
        raise ValueError("dt_seconds must be > 0")
    total_umol = sum(ppfd_series) * dt_seconds  # μmol m^-2 per day-window
    return total_umol / 1e6  # mol m^-2 d^-1


def dim_for_target_ppfd(target_ppfd: float, ppfd_max: float, min_dim: float = 0.0) -> float:
    """
    Convert desired PPFD into a dimming fraction given fixture PPFD_max at canopy.
    """
    if ppfd_max <= 0:
        raise ValueError("ppfd_max must be > 0")
    frac = target_ppfd / ppfd_max
    return clamp(frac, min_dim, 1.0)


def dli_controller_step(dli_target: float,
                        dli_so_far: float,
                        seconds_left_in_window: float,
                        ppfd_minmax: Tuple[float, float]) -> float:
    """
    Compute the required *average* PPFD for the remainder of the light window
    to hit the DLI target. Returns the PPFD setpoint (clamped to min/max).
    """
    ppfd_min, ppfd_max = ppfd_minmax
    ppfd_min = max(0.0, ppfd_min)
    ppfd_max = max(ppfd_max, ppfd_min + 1e-6)

    remaining_umol = max(0.0, (dli_target - dli_so_far)) * 1e6
    if seconds_left_in_window <= 0:
        # Window closed; cannot catch up
        return ppfd_min
    needed_ppfd = remaining_umol / seconds_left_in_window
    return clamp(needed_ppfd, ppfd_min, ppfd_max)


@dataclass
class LightFixture:
    """Convenience wrapper to compute PPFD, power, and heat for a given dimming level."""
    ppf_max: float                 # μmol/s emitted at 100% (nameplate)
    ppe: float                     # μmol/J nominal
    area_m2: float                 # illuminated area
    spectrum: Dict[str, float]     # fractional weights (e.g., {"B":0.1,"G":0.2,"R":0.6,"FR":0.1})
    driver_loss: float = 0.04
    thermal_derate: float = 0.0
    wall_reflectance: float = 0.85
    beam_spread_deg: float = 120.0

    def step(self, dim_frac: float, LAI: float) -> Dict[str, float]:
        ppf = ppf_from_dim(dim_frac, self.ppf_max)
        bands = mix_spectrum(ppf, self.spectrum)
        u = utilization_factor(LAI, self.wall_reflectance, self.beam_spread_deg)
        ppfd = ppfd_at_canopy(ppf, u, self.area_m2)
        win, heat = electrical_watts(ppf, self.ppe, self.driver_loss, self.thermal_derate)
        return {
            "ppf_total": ppf,
            "ppfd": ppfd,
            "u": u,
            "bands_ppf": bands,
            "watts_in": win,
            "heat_watts": heat
        }