from multistep.refiner import refine_query


def test_refine_missing_year():
    result = refine_query("Revenue in 2020 and 2021", "MISSING_YEAR", ["2021"], None)
    assert "2021" in result.refined_query


def test_refine_missing_entity():
    result = refine_query("Compare MS vs GS", "MISSING_ENTITY", [], "GS")
    assert "GS" in result.refined_query
