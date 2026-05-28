# astro_utils.py
import swisseph as swe
from datetime import datetime, timezone
from dateutil import parser
import pytz

NAK_N = 28
NAK_WIDTH = 360.0 / NAK_N

PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Rahu': swe.MEAN_NODE,
}

RASHI_LORD = {
    0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
    4: 'Sun', 5: 'Mercury', 6: 'Venus', 7: 'Mars',
    8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
}

def rashi_from_long(lon):
    return int((lon % 360.0) // 30)

def nakshatra_index_from_long(lon):
    lon = lon % 360.0
    return int(lon // NAK_WIDTH)

def julian_day_from_datetime(dt):
    year = dt.year; month = dt.month; day = dt.day
    frac_hours = dt.hour + dt.minute/60.0 + dt.second/3600.0 + dt.microsecond/(3600.0*1e6)
    return swe.julday(year, month, day, frac_hours)

def planetary_longitudes(jd_ut):
    longs = {}
    for name, pid in PLANETS.items():
        if name == 'Rahu':
            arr = swe.calc_ut(jd_ut, pid)
            lon = arr[0][0] if isinstance(arr[0], (list, tuple)) else arr[0]
            longs['Rahu'] = lon % 360.0
            longs['Ketu'] = (lon + 180.0) % 360.0
        else:
            arr = swe.calc_ut(jd_ut, pid)
            lon = arr[0][0] if isinstance(arr[0], (list, tuple)) else arr[0]
            longs[name] = lon % 360.0
    return longs

def pada_of_long(lon):
    pos_in_nak = (lon % NAK_WIDTH)
    pada_size = NAK_WIDTH / 4.0
    pada = int(pos_in_nak // pada_size) + 1
    return max(1, min(4, pada))

def pada_midpoint_longitude(nak_index, pada):
    nak_start = nak_index * NAK_WIDTH
    pada_width = NAK_WIDTH / 4.0
    pada_start = nak_start + (pada - 1) * pada_width
    return ((pada_start + (pada_start + pada_width)) / 2.0) % 360.0

def avakhada_pada_lord_from_nak_and_pada(nak_index, pada):
    mid = pada_midpoint_longitude(nak_index, pada)
    rashi_idx = rashi_from_long(mid)
    return RASHI_LORD.get(rashi_idx)

def natal_moon_nakshatra_index(dob_iso):
    dt = parser.isoparse(dob_iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)
    jd = julian_day_from_datetime(dt_utc)
    arr = swe.calc_ut(jd, swe.MOON)
    lon = arr[0][0] if isinstance(arr[0], (list, tuple)) else arr[0]
    return nakshatra_index_from_long(lon % 360.0)
