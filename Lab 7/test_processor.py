from hypothesis import given, strategies as st
from processor import parse_walk_schedule, compute_pace_per_pet, lookup_temperament_surcharge

@given(st.text() | st.none())
def test_parse_walk_schedule_no_crash(s):
    try:
        parse_walk_schedule(s)
    except Exception as e:
        assert False, f"parse_walk_schedule crashed with: {e}"

@given(st.text() | st.none())
def test_compute_pace_per_pet_safe(s):
    try:
        compute_pace_per_pet(s)
    except Exception as e:
        assert False, f"compute_pace_per_pet crashed with: {e}"

@given(st.text() | st.none())
def test_lookup_temperament_surcharge_safe(s):
    try:
        lookup_temperament_surcharge(s)
    except Exception as e:
        assert False, f"lookup_temperament_surcharge crashed with: {e}"
