"""
Photoperiod + dimming controller to hit a target DLI.
Adjusts LED dimming fraction intra-day to ensure DLI target is met by end of light window.
"""

def dli_controller_step(dli_target, dli_so_far, seconds_left_in_window, ppfd_minmax):
    """
    Compute the required average PPFD for the remainder of the light window
    to hit the DLI target. Returns the PPFD setpoint (clamped to min/max).
    Args:
        dli_target: target daily light integral (mol/m2/d)
        dli_so_far: DLI accumulated so far (mol/m2/d)
        seconds_left_in_window: seconds remaining in the photoperiod
        ppfd_minmax: (min, max) allowable PPFD (μmol/m2/s)
    Returns:
        needed_ppfd: PPFD setpoint for the next step (μmol/m2/s)
    """
    ppfd_min, ppfd_max = ppfd_minmax
    ppfd_min = max(0.0, ppfd_min)
    ppfd_max = max(ppfd_max, ppfd_min + 1e-6)

    remaining_umol = max(0.0, (dli_target - dli_so_far)) * 1e6
    if seconds_left_in_window <= 0:
        # Window closed; cannot catch up
        return ppfd_min
    needed_ppfd = remaining_umol / seconds_left_in_window
    return max(ppfd_min, min(needed_ppfd, ppfd_max))
