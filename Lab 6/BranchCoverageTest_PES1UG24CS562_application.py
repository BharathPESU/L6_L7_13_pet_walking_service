import pytest
from pet_walking_service import process_walking_routes, inspect_gps_collars


# ==============================================================================
# Branch Coverage Test Suite for process_walking_routes
# Target: Test all true/false decision branches, boundary values & edge cases
# ==============================================================================

def test_routes_not_a_list_branch():
    """Branch: not isinstance(routes, list) is True"""
    with pytest.raises(ValueError, match="Invalid routes list or transport fee"):
        process_walking_routes("invalid_string_not_a_list", 10.0)


def test_negative_transport_fee_branch():
    """Branch: not isinstance(routes, list) is False, base_transport_fee < 0 is True"""
    with pytest.raises(ValueError, match="Invalid routes list or transport fee"):
        process_walking_routes([], -0.01)


def test_empty_routes_list_branch():
    """Branch: routes loop is empty (0 iterations) -> finishes with total_revenue == 0.0"""
    result = process_walking_routes([], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_EARNINGS"}


def test_unconfirmed_route_branch():
    """Branch: route_confirmed is False -> continues loop"""
    routes = [
        {
            "route_confirmed": False,
            "session_type": "standard_30",
            "walks": [{"num_pets": 2, "aggression_alert": False, "needs_meds": False}],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_EARNINGS"}


def test_session_type_standard_60_weekend_branch():
    """
    Branches:
    - session_type == 'standard_60' (base_fee = 35.0)
    - num_pets <= 3 (num_pets * 5.0)
    - needs_meds is False
    - is_weekend is True (+base_transport_fee)
    - total_revenue != 0.0 and incident_count <= 4 -> COMPLETED
    """
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_60",
            "is_weekend": True,
            "walks": [{"num_pets": 2, "aggression_alert": False, "needs_meds": False}],
        }
    ]
    # base_fee (35.0) + pets (2 * 5.0 = 10.0) + weekend (10.0) = 55.0
    result = process_walking_routes(routes, 10.0)
    assert result == {"total_revenue": 55.0, "status": "COMPLETED"}


def test_session_type_standard_30_branch():
    """
    Branches:
    - session_type == 'standard_30' (base_fee = 22.0)
    - is_weekend is False
    """
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "is_weekend": False,
            "walks": [{"num_pets": 1, "aggression_alert": False, "needs_meds": False}],
        }
    ]
    # base_fee (22.0) + pets (1 * 5.0 = 5.0) = 27.0
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 27.0, "status": "COMPLETED"}


def test_session_type_express_15_branch():
    """
    Branches:
    - session_type == 'express_15' (base_fee = 14.0)
    - is_weekend is False
    """
    routes = [
        {
            "route_confirmed": True,
            "session_type": "express_15",
            "is_weekend": False,
            "walks": [{"num_pets": 1, "aggression_alert": False, "needs_meds": False}],
        }
    ]
    # base_fee (14.0) + pets (1 * 5.0 = 5.0) = 19.0
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 19.0, "status": "COMPLETED"}


def test_invalid_session_type_branch():
    """Branch: session_type else (invalid type) -> incident_count += 1, continue"""
    routes = [
        {
            "route_confirmed": True,
            "session_type": "luxury_90",
            "walks": [{"num_pets": 1}],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_EARNINGS"}


def test_empty_walks_list_branch():
    """Branch: route confirmed, but walks list is empty (0 walks executed)"""
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "is_weekend": False,
            "walks": [],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_EARNINGS"}


def test_walk_num_pets_zero_and_negative_boundary():
    """Branch: num_pets <= 0 is True (boundary testing with 0 and negative value)"""
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "walks": [
                {"num_pets": 0, "aggression_alert": False},
                {"num_pets": -2, "aggression_alert": False},
            ],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_EARNINGS"}


def test_aggression_alert_in_standard_60_breaks_route():
    """
    Branches:
    - aggression_alert is True
    - session_type == 'standard_60' is True -> route_earnings = 0.0, break
    """
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_60",
            "is_weekend": False,
            "walks": [
                {"num_pets": 2, "aggression_alert": True, "needs_meds": False},
                {"num_pets": 1, "aggression_alert": False, "needs_meds": False},
            ],
        }
    ]
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_EARNINGS"}


def test_aggression_alert_in_non_standard_60():
    """
    Branches:
    - aggression_alert is True
    - session_type == 'standard_60' is False -> route_earnings += 0.0 (continues next walk)
    """
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "is_weekend": False,
            "walks": [
                {"num_pets": 2, "aggression_alert": True, "needs_meds": False},
                {"num_pets": 1, "aggression_alert": False, "needs_meds": False},
            ],
        }
    ]
    # Walk 1 adds 0.0; Walk 2 adds 22.0 + 5.0 = 27.0
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 27.0, "status": "COMPLETED"}


def test_num_pets_greater_than_3_discount_and_meds():
    """
    Branches:
    - aggression_alert is False
    - num_pets > 3 is True -> (base_fee + num_pets * 8.0) * 0.90
    - needs_medication is True -> route_earnings += 6.0
    """
    routes = [
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "is_weekend": False,
            "walks": [
                {"num_pets": 5, "aggression_alert": False, "needs_meds": True}
            ],
        }
    ]
    # base_fee (22.0) + (5 * 8.0 = 40.0) = 62.0 * 0.90 = 55.80 + 6.0 = 61.80
    result = process_walking_routes(routes, 5.0)
    assert result == {"total_revenue": 61.80, "status": "COMPLETED"}


def test_incident_count_greater_than_four_audit():
    """Branch: incident_count > 4 is True -> status: 'INCIDENT_AUDIT'"""
    routes = [
        {"route_confirmed": True, "session_type": "inv1", "walks": []},
        {"route_confirmed": True, "session_type": "inv2", "walks": []},
        {"route_confirmed": True, "session_type": "inv3", "walks": []},
        {"route_confirmed": True, "session_type": "inv4", "walks": []},
        {"route_confirmed": True, "session_type": "inv5", "walks": []},
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["status"] == "INCIDENT_AUDIT"


def test_incident_count_exactly_four_not_audit():
    """Branch boundary: incident_count == 4 (not > 4) -> proceeds to normal status check"""
    routes = [
        {"route_confirmed": True, "session_type": "inv1", "walks": []},
        {"route_confirmed": True, "session_type": "inv2", "walks": []},
        {"route_confirmed": True, "session_type": "inv3", "walks": []},
        {"route_confirmed": True, "session_type": "inv4", "walks": []},
        {
            "route_confirmed": True,
            "session_type": "standard_30",
            "is_weekend": False,
            "walks": [{"num_pets": 1, "aggression_alert": False, "needs_meds": False}],
        },
    ]
    result = process_walking_routes(routes, 5.0)
    assert result["status"] == "COMPLETED"


# ==============================================================================
# Branch Coverage Test Suite for inspect_gps_collars
# Target: Empty check, streak increments, streak reset, alert trigger & online
# ==============================================================================

def test_inspect_gps_collars_empty_or_none():
    """Branch: not collar_matrix is True (both empty list and None)"""
    assert inspect_gps_collars([]) == "NO_DATA"
    assert inspect_gps_collars(None) == "NO_DATA"


def test_inspect_gps_collars_empty_sublist():
    """Branch: collar_logs loop has 0 iterations"""
    assert inspect_gps_collars([[]]) == "ONLINE"


def test_inspect_gps_collars_single_low_signal_no_alert():
    """
    Branches:
    - signal_strength < 20 is True (signal_lost_streak becomes 1)
    - signal_lost_streak >= 2 is False
    - signal_strength >= 20 is True (resets signal_lost_streak to 0)
    - loop completes -> returns 'ONLINE'
    """
    matrix = [
        [15, 25, 18, 90]
    ]
    assert inspect_gps_collars(matrix) == "ONLINE"


def test_inspect_gps_collars_two_consecutive_low_signals_alert():
    """
    Branches:
    - signal_strength < 20 is True twice consecutively
    - signal_lost_streak >= 2 is True -> returns 'LOST_SIGNAL_ALERT'
    """
    matrix = [
        [50, 19, 10, 80]
    ]
    assert inspect_gps_collars(matrix) == "LOST_SIGNAL_ALERT"


def test_inspect_gps_collars_multiple_collars_all_good():
    """Branch: Multiple collars all with strong signals -> returns 'ONLINE'"""
    matrix = [
        [50, 60, 70],
        [80, 85, 90],
    ]
    assert inspect_gps_collars(matrix) == "ONLINE"
