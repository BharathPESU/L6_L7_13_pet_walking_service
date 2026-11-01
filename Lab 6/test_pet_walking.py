import pytest
from pet_walking_service import process_walking_routes, inspect_gps_collars


# --- Tests for process_walking_routes ---

def test_single_standard_30_walk():
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "is_weekend": False,
            "walks": [{"num_pets": 1, "aggression_alert": False, "needs_meds": False}],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 27.0
    assert result["status"] == "COMPLETED"


def test_invalid_routes_input():
    with pytest.raises(ValueError, match="Invalid routes list or transport fee"):
        process_walking_routes("not_a_list", 5.0)


def test_negative_transport_fee():
    with pytest.raises(ValueError, match="Invalid routes list or transport fee"):
        process_walking_routes([], -1.0)


def test_unconfirmed_route_skipped():
    routes = [
        {
            "route_confirmed": False,
            "session_type": "standard_30",
            "walks": [{"num_pets": 1}],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 0.0
    assert result["status"] == "ZERO_EARNINGS"


def test_session_type_standard_60_and_weekend():
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_60",
            "is_weekend": True,
            "walks": [{"num_pets": 2, "aggression_alert": False, "needs_meds": False}],
        }
    ]
    # base_fee = 35.0, pets = 2 * 5.0 = 10.0, weekend transport fee = 5.0 -> 35 + 10 + 5 = 50.0
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 50.0
    assert result["status"] == "COMPLETED"


def test_session_type_express_15():
    routes = [
        {
            "route_confirmed": True,
            "session_type": "express_15",
            "is_weekend": False,
            "walks": [{"num_pets": 1, "aggression_alert": False, "needs_meds": False}],
        }
    ]
    # base_fee = 14.0, pets = 1 * 5.0 = 5.0 -> 19.0
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 19.0
    assert result["status"] == "COMPLETED"


def test_invalid_session_type():
    routes = [
        {
            "route_confirmed": True,
            "session_type": "unknown_type",
            "walks": [{"num_pets": 1}],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 0.0
    assert result["status"] == "ZERO_EARNINGS"


def test_walk_with_zero_or_negative_pets():
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "walks": [{"num_pets": 0}],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 0.0
    assert result["status"] == "ZERO_EARNINGS"


def test_aggression_alert_in_standard_60():
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_60",
            "is_weekend": False,
            "walks": [
                {"num_pets": 2, "aggression_alert": True, "needs_meds": False}
            ],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 0.0
    assert result["status"] == "ZERO_EARNINGS"


def test_aggression_alert_in_standard_30():
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "is_weekend": False,
            "walks": [
                {"num_pets": 2, "aggression_alert": True, "needs_meds": False}
            ],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 0.0
    assert result["status"] == "ZERO_EARNINGS"


def test_more_than_three_pets_and_medication():
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "is_weekend": False,
            "walks": [
                {"num_pets": 4, "aggression_alert": False, "needs_meds": True}
            ],
        }
    ]
    # base_fee = 22.0, num_pets = 4 -> (22 + 32) * 0.90 = 54 * 0.9 = 48.60
    # meds = +6.0 -> 48.60 + 6.0 = 54.60
    result = process_walking_routes(routes, 5.0)
    assert result["total_revenue"] == 54.60
    assert result["status"] == "COMPLETED"


def test_incident_audit_status():
    routes = [
        {"route_confirmed": True, "session_type": "invalid_1", "walks": []},
        {"route_confirmed": True, "session_type": "invalid_2", "walks": []},
        {"route_confirmed": True, "session_type": "invalid_3", "walks": []},
        {"route_confirmed": True, "session_type": "invalid_4", "walks": []},
        {"route_confirmed": True, "session_type": "invalid_5", "walks": []},
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["status"] == "INCIDENT_AUDIT"


# --- Tests for inspect_gps_collars ---

def test_inspect_gps_collars_empty():
    assert inspect_gps_collars([]) == "NO_DATA"
    assert inspect_gps_collars(None) == "NO_DATA"


def test_inspect_gps_collars_lost_signal_alert():
    matrix = [
        [50, 15, 10, 80]  # two consecutive signals < 20
    ]
    assert inspect_gps_collars(matrix) == "LOST_SIGNAL_ALERT"


def test_inspect_gps_collars_online_with_recovery():
    matrix = [
        [15, 25, 10, 30],  # low signals separated by good signals (resets streak)
        [50, 60, 70]
    ]
    assert inspect_gps_collars(matrix) == "ONLINE"