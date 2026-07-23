"""
add_habitability_score.py

Adds TWO new columns to the exoplanet dataset:
    - habitability_score : numeric score (0-15) from weighted criteria
    - habitability_class : 'Potentially Habitable' / 'Possibly Habitable' / 'Non-Habitable'

Based on a weighted rule system over the planet/star properties actually
available in the NASA Exoplanet Archive export (pl_rade, pl_masse, pl_dens,
pl_eqt, pl_insol, pl_orbeccen, st_spectype, st_age).

NOTE: The dataset does NOT contain atmospheric molecule detections
(NOTE/MINWAVELNG/MAXWAVELNG/SPEC_TYPE are observation metadata, not
composition data), so the "water detected" bonus from the original scoring
table is implemented as an optional hook only -- it contributes 0 unless you
merge in a real atmosphere-composition column and set WATER_COLUMN below.

Usage:
    python add_habitability_score.py input.csv output.csv
"""

import re
import sys
import pandas as pd


# ----------------------------------------------------------------------
# Optional: set this to a column name (e.g. "water_detected") containing
# True/False if you later merge in real atmosphere-composition data.
# Leave as None to skip this bonus entirely (matches current dataset).
# ----------------------------------------------------------------------
WATER_COLUMN = None
WATER_BONUS = 3

# Points awarded when a criterion is satisfied
POINTS = {
    "radius": 2,     # pl_rade in [0.8, 1.8] Earth radii
    "mass": 2,       # pl_masse in [0.5, 5] Earth masses
    "temperature": 3,  # pl_eqt in [180, 320] K
    "insolation": 3,   # pl_insol in [0.3, 1.8] Earth flux
    "density": 2,      # pl_dens > 3 g/cm^3
    "eccentricity": 1, # pl_orbeccen < 0.3
    "star_type": 1,    # spectral type F, G, K, or early M (M0-M5)
    "age": 1,          # st_age > 1 Gyr
}

MAX_SCORE = sum(POINTS.values()) + (WATER_BONUS if WATER_COLUMN else 0)

# Classification thresholds, scaled proportionally from the original
# 18-point scale (15-18 / 10-14 / 0-9) to whatever MAX_SCORE actually is.
POTENTIALLY_HABITABLE_CUTOFF = round(MAX_SCORE * (15 / 18))
POSSIBLY_HABITABLE_CUTOFF = round(MAX_SCORE * (10 / 18))


def in_range(value, low, high):
    return pd.notna(value) and low <= value <= high


def is_early_fgk_star(spectype):
    if pd.isna(spectype):
        return False
    spectype = str(spectype).strip().upper()
    match = re.match(r"^([OBAFGKM])(\d(\.\d)?)?", spectype)
    if not match:
        return False
    letter = match.group(1)
    if letter in ("F", "G", "K"):
        return True
    if letter == "M":
        number = match.group(2)
        # "Early M" ~ M0-M5
        if number is None:
            return False
        return float(number) <= 5.0
    return False


def score_row(row):
    score = 0
    details = {}

    if in_range(row.get("pl_rade"), 0.8, 1.8):
        score += POINTS["radius"]
        details["radius"] = True
    else:
        details["radius"] = False

    if in_range(row.get("pl_masse"), 0.5, 5.0):
        score += POINTS["mass"]
        details["mass"] = True
    else:
        details["mass"] = False

    if in_range(row.get("pl_eqt"), 180, 320):
        score += POINTS["temperature"]
        details["temperature"] = True
    else:
        details["temperature"] = False

    if in_range(row.get("pl_insol"), 0.3, 1.8):
        score += POINTS["insolation"]
        details["insolation"] = True
    else:
        details["insolation"] = False

    density = row.get("pl_dens")
    if pd.notna(density) and density > 3:
        score += POINTS["density"]
        details["density"] = True
    else:
        details["density"] = False

    eccen = row.get("pl_orbeccen")
    if pd.notna(eccen) and eccen < 0.3:
        score += POINTS["eccentricity"]
        details["eccentricity"] = True
    else:
        details["eccentricity"] = False

    if is_early_fgk_star(row.get("st_spectype")):
        score += POINTS["star_type"]
        details["star_type"] = True
    else:
        details["star_type"] = False

    age = row.get("st_age")
    if pd.notna(age) and age > 1.0:  # st_age is in Gyr in this dataset
        score += POINTS["age"]
        details["age"] = True
    else:
        details["age"] = False

    if WATER_COLUMN and WATER_COLUMN in row and bool(row[WATER_COLUMN]):
        score += WATER_BONUS
        details["water"] = True
    elif WATER_COLUMN:
        details["water"] = False

    return score, details


def classify(score):
    if score >= POTENTIALLY_HABITABLE_CUTOFF:
        return "Potentially Habitable"
    elif score >= POSSIBLY_HABITABLE_CUTOFF:
        return "Possibly Habitable"
    else:
        return "Non-Habitable"


def main():
    if len(sys.argv) != 3:
        print("Usage: python add_habitability_score.py <input_csv> <output_csv>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]
    df = pd.read_csv(input_path)

    scores = []
    classes = []
    for _, row in df.iterrows():
        score, _ = score_row(row)
        scores.append(score)
        classes.append(classify(score))

    df["habitability_score"] = scores
    df["habitability_class"] = classes

    df.to_csv(output_path, index=False)

    print(f"Max possible score: {MAX_SCORE}")
    print(f"Potentially Habitable cutoff: >= {POTENTIALLY_HABITABLE_CUTOFF}")
    print(f"Possibly Habitable cutoff:    >= {POSSIBLY_HABITABLE_CUTOFF}")
    print()
    print("Summary:")
    print(df["habitability_class"].value_counts().to_string())
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
