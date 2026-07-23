"""
habitability_v2.py

Adds these new columns to the exoplanet dataset:

    esi                      : Earth Similarity Index, 0-1 (Schulze-Makuch et al. 2011)
    habitability_category    : 4-tier category derived from ESI
    planet_type               : Rocky / Super-Earth / Sub-Neptune / Neptune-like / Gas Giant
                                 (based on radius & mass, standard exoplanet-science thresholds)
    inferred_atmosphere       : A PLAUSIBLE atmosphere type, inferred from planet_type + temperature.
                                 *** This is a hypothesis, NOT a real measured detection. ***
                                 The dataset has no actual gas/molecule detection column --
                                 SPEC_TYPE/NOTE/MINWAVELNG/MAXWAVELNG are observation metadata only
                                 (instrument, spectral mode, wavelength coverage, reduction pipeline
                                 notes) -- not composition data. Verified by keyword search: every
                                 apparent match for gas names in NOTE (e.g. "TiO") turned out to be a
                                 substring of an unrelated word (e.g. "ExoTiC-JEDI", a pipeline name).

Why ESI instead of an arbitrary point system:
    ESI is a real, published, peer-reviewed astrobiology metric (Schulze-Makuch et al. 2011,
    "A Two-Tiered Approach to Assessing the Habitability of Exoplanets"), used in actual
    literature/catalogs (e.g. PHL's Habitable Exoplanets Catalog). It compares each planet
    property to Earth's value using a geometric-mean similarity formula, rather than made-up
    point weights.

    ESI_i    = (1 - |x_i - x_earth| / (x_i + x_earth)) ^ (w_i / n)
    ESI_interior = sqrt(ESI_radius * ESI_density)
    ESI_surface  = sqrt(ESI_escape_velocity * ESI_temperature)
    ESI          = sqrt(ESI_interior * ESI_surface)

    Reference values (Earth = 1 in relative units):
        radius            = 1 Earth radius
        density           = 5.51 g/cm^3
        escape velocity   = 11.19 km/s
        surface temp      = 288 K   (dataset's pl_eqt used as the closest available proxy)

    Published weights (n=4 properties): radius=0.57, density=1.07, escape velocity=0.70, temp=5.58

Usage:
    python habitability_v2.py input.csv output.csv
"""

import math
import sys
import pandas as pd


# ---------------------------------------------------------------
# Earth reference values and ESI weights (from Schulze-Makuch et al. 2011)
# ---------------------------------------------------------------
EARTH_RADIUS = 1.0          # Earth radii
EARTH_DENSITY = 5.51        # g/cm^3
EARTH_ESC_VEL = 11.19       # km/s
EARTH_TEMP = 288.0          # K

WEIGHTS = {
    "radius": 0.57,
    "density": 1.07,
    "esc_vel": 0.70,
    "temp": 5.58,
}
N_PROPERTIES = 4


def esi_component(value, reference, weight):
    if pd.isna(value) or value <= 0:
        return None
    ratio_term = abs(value - reference) / (value + reference)
    return (1 - ratio_term) ** (weight / N_PROPERTIES)


def compute_escape_velocity_ratio(mass_earth, radius_earth):
    """Escape velocity relative to Earth: v_esc / v_esc_earth = sqrt(M/R) in Earth units."""
    if pd.isna(mass_earth) or pd.isna(radius_earth) or radius_earth <= 0:
        return None
    return math.sqrt(mass_earth / radius_earth) * EARTH_ESC_VEL


def compute_esi(row):
    radius = row.get("pl_rade")
    density = row.get("pl_dens")
    mass = row.get("pl_masse")
    temp = row.get("pl_eqt")

    esc_vel = compute_escape_velocity_ratio(mass, radius)

    esi_radius = esi_component(radius, EARTH_RADIUS, WEIGHTS["radius"])
    esi_density = esi_component(density, EARTH_DENSITY, WEIGHTS["density"])
    esi_escvel = esi_component(esc_vel, EARTH_ESC_VEL, WEIGHTS["esc_vel"])
    esi_temp = esi_component(temp, EARTH_TEMP, WEIGHTS["temp"])

    interior_parts = [x for x in (esi_radius, esi_density) if x is not None]
    surface_parts = [x for x in (esi_escvel, esi_temp) if x is not None]

    # Need at least one property from each half (interior + surface) to compute anything meaningful
    if not interior_parts or not surface_parts:
        return None

    esi_interior = math.prod(interior_parts) ** (1 / len(interior_parts))
    esi_surface = math.prod(surface_parts) ** (1 / len(surface_parts))

    return math.sqrt(esi_interior * esi_surface)


def esi_to_category(esi):
    if esi is None:
        return "Insufficient Data"
    if esi >= 0.8:
        return "Earth-like (High Habitability Potential)"
    elif esi >= 0.6:
        return "Moderately Habitable"
    elif esi >= 0.4:
        return "Marginally Habitable"
    else:
        return "Non-Habitable"


def classify_planet_type(radius, mass):
    """Standard radius/mass-based exoplanet classification bins used across exoplanet science."""
    if pd.isna(radius):
        return "Unknown"
    if radius < 1.5:
        return "Rocky"
    elif radius < 2.0:
        return "Super-Earth"
    elif radius < 4.0:
        return "Sub-Neptune"
    elif radius < 10.0:
        return "Neptune-like"
    else:
        return "Gas Giant"


def infer_atmosphere(planet_type, temp):
    """
    Physically-motivated HYPOTHESIS about likely dominant atmosphere type.
    NOT a real detection -- this dataset contains no measured gas/molecule data.
    Based on standard exoplanet formation/atmosphere-retention science:
      - Large planets retain primordial H/He envelopes.
      - Small, hot rocky planets tend to lose primary atmospheres and may
        retain only thin secondary atmospheres (CO2/N2) or none at all.
      - Extremely hot planets (>1000K) risk atmospheric escape / exotic
        vaporized-rock atmospheres.
    """
    if planet_type == "Unknown":
        return "Unknown (insufficient data)"

    if planet_type == "Gas Giant":
        return "Inferred: H/He-dominated primordial envelope"

    if planet_type == "Neptune-like":
        return "Inferred: H/He + volatile ices (Neptune-like envelope)"

    if planet_type == "Sub-Neptune":
        if pd.notna(temp) and temp > 800:
            return "Inferred: H/He envelope likely eroding (highly irradiated)"
        return "Inferred: possible H/He or steam/volatile-rich envelope"

    # Rocky or Super-Earth
    if pd.isna(temp):
        return "Inferred: thin secondary atmosphere (temperature unknown)"
    if temp > 1000:
        return "Inferred: atmosphere likely stripped / exotic vapor (extreme heat)"
    elif temp > 500:
        return "Inferred: thin or no atmosphere (too hot for stable volatiles)"
    elif 180 <= temp <= 320:
        return "Inferred: possible CO2/N2/H2O secondary atmosphere (temperate)"
    else:
        return "Inferred: thin atmosphere or frozen volatiles (cold)"

import sys
import pandas as pd
import numpy as np

def main():
    if len(sys.argv) != 3:
        print("Usage: python habitability_v2.py <input_csv> <output_csv>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    df = pd.read_csv(input_path)

    # Compute Earth Similarity Index (ESI)
    
    esi_values: pd.Series = df.apply(compute_esi, axis=1)

    df["esi"] = esi_values
    df["habitability_category"] = esi_values.apply(esi_to_category)

    df["planet_type"] = df.apply(
        lambda row: classify_planet_type(
            row.get("pl_rade"),
            row.get("pl_masse"),
        ),
        axis=1,
    )

    df["inferred_atmosphere"] = df.apply(
        lambda row: infer_atmosphere(
            row["planet_type"],
            row.get("pl_eqt"),
        ),
        axis=1,
    )

    df.to_csv(output_path, index=False)

    print("\nHabitability category counts:")
    print(df["habitability_category"].value_counts(dropna=False).to_string())

    print("\nPlanet type counts:")
    print(df["planet_type"].value_counts(dropna=False).to_string())

    print("\nTop 10 by ESI:")

    top = (
        df.dropna(subset=["esi"])
          .sort_values("esi", ascending=False)
          .drop_duplicates(subset="pl_name")
          .head(10)
    )

    print(
        top[
            [
                "pl_name",
                "esi",
                "habitability_category",
                "planet_type",
                "inferred_atmosphere",
            ]
        ].to_string(index=False)
    )

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()