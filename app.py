from math import hypot


def coordinate(point, key):
    value = point[key]
    if type(value) not in (int, float) or not -100_000_000 <= value <= 100_000_000:
        raise ValueError(f"{key} must be a finite planar coordinate within 100 million meters")
    return value


def point_xy(point):
    return coordinate(point, "east_m"), coordinate(point, "north_m")


def analyze(data):
    start_east, start_north = point_xy(data["start"])
    end_east, end_north = point_xy(data["end"])
    east, north = end_east - start_east, end_north - start_north
    length = hypot(east, north)
    if length < 0.001:
        raise ValueError("transect endpoints must be at least 1 millimeter apart")
    unit_east, unit_north = east / length, north / length
    end_station = round(length, 3)
    raw = data["points"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= 1000:
        raise ValueError("enter 1 through 1000 observation points")

    readings = []
    seen = set()
    for point in raw:
        name = point["name"]
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError("point names must be nonempty labels of at most 80 characters")
        name = name.strip()
        if name in seen:
            raise ValueError("point names must be unique")
        seen.add(name)
        p_east, p_north = point_xy(point)
        delta_east, delta_north = p_east - start_east, p_north - start_north
        station = unit_east * delta_east + unit_north * delta_north
        offset = unit_east * delta_north - unit_north * delta_east
        reported_station = round(station, 3)
        reach = "within"
        if reported_station < 0:
            reach = "before"
        elif reported_station > end_station:
            reach = "beyond"
        readings.append({"point": name, "station_m": reported_station,
                         "left_offset_m": round(offset, 3), "reach": reach,
                         "projection_east_m": round(start_east + station * unit_east, 3),
                         "projection_north_m": round(start_north + station * unit_north, 3)})

    return {"transect_length_m": end_station, "point_count": len(readings),
            "points_outside_segment": sum(point["reach"] != "within" for point in readings),
            "readings": readings}

if __name__ == "__main__":
    import json
    from pathlib import Path
    import sys
    try:
        path, = sys.argv[1:]
        result = analyze(json.loads(Path(path).read_text(encoding="utf-8")))
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        sys.exit(2)
