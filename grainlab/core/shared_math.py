def f_to_c(f: float) -> float:
    return round((f - 32.0) * 5.0 / 9.0, 1)


def c_to_f(c: float) -> float:
    return round((c * 9.0 / 5.0) + 32.0, 1)


def scale_baking_profile(base_temp: float, base_time: float, base_weight: float, target_mass: float, is_portioned: bool) -> tuple[float, float]:
    """
    Algorithmically scale baking profile (temperature and time) based on mass and form factor.
    """
    mass_ratio = target_mass / base_weight if base_weight > 0 else 1.0
    scaled_time = round(base_time * (mass_ratio ** 0.4))
    
    scaled_temp = base_temp
    if not is_portioned:
        if mass_ratio > 1.2:
            scaled_temp = base_temp - 10
        elif mass_ratio < 0.8:
            scaled_temp = base_temp + 10
            
    return scaled_temp, scaled_time


def calculate_yield_mass(is_portioned: bool, unit_weight: float, portion_count: int, target_weight: float) -> float:
    """
    Dynamic yield multiplier logic. Calculates total target mass of the recipe.
    """
    if is_portioned:
        return unit_weight * portion_count
    return target_weight
