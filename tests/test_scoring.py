from benchmark.scoring.entities_match import match


def test_entity_matching_raw_vs_normalized():
    assert match({"type": "phone", "value": "9848012345"}, "నా number 98480 12345") == (True, True, "ok")
    assert match({"type": "phone", "value": "9848012345"}, "nine eight four eight zero one two three four five")[1:] == (True, "ok")
    assert match({"type": "phone", "value": "9848012345"}, "98480 12346")[2] == "wrong_value"
    assert match({"type": "vehicle_reg", "value": "TS09EA4521"}, "TS 09 EA 4521 బండి")[:2] == (True, True)
    assert match({"type": "vehicle_reg", "value": "TS09EA4521"}, "TS 09 AE 4521")[2] == "wrong_value"
    assert match({"type": "date", "value": "weekday:4"}, "Wednesday కాదు కాదు Friday")[1]
    assert match({"type": "time", "value": "17:30"}, "సాయంత్రం ఐదున్నరకి")[1]
    assert match({"type": "person", "value": "Srinivas Reddy"}, "శ్రీనివాస్ రెడ్డి గారితో")[1]
    assert match({"type": "person", "value": "Srinivas Reddy"}, "Srinivas Rao garu")[2] == "wrong_value"
    assert match({"type": "price", "value": 1899}, "₹1,899 అన్నారు")[1]
