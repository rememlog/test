from backend.app.services.analysis import analyze_entries
from backend.app.services.kra import extract_items, normalize_entry


def test_extract_and_normalize_entry_sheet_response():
    payload = {
        "response": {
            "body": {
                "items": {
                    "item": [
                        {
                            "meet": "서울",
                            "rcDate": "20260822",
                            "rcNo": 7,
                            "rcDist": 1400,
                            "chulNo": 5,
                            "hrNo": "004321",
                            "hrName": "테스트말",
                            "jkNo": "090001",
                            "jkName": "테스트기수",
                            "trNo": "070001",
                            "trName": "테스트조교사",
                            "owNo": "050001",
                            "owName": "테스트마주",
                            "rating": 75,
                            "rcCntT": 20,
                            "ord1CntT": 4,
                            "ord2CntT": 3,
                            "ord3CntT": 2,
                            "rcCntY": 8,
                            "ord1CntY": 2,
                            "ord2CntY": 1,
                            "ord3CntY": 1,
                            "chaksunY": 50000000,
                        }
                    ]
                }
            }
        }
    }
    rows = extract_items(payload)
    entry = normalize_entry(rows[0])
    assert entry.race_id == "서울-20260822-07"
    assert entry.horse_name == "테스트말"
    assert entry.recent_year_starts == 8


def test_baseline_analysis_probabilities_sum_to_one():
    rows = [
        normalize_entry({"meet":"서울","rcDate":"20260822","rcNo":7,"hrNo":"1","hrName":"A","rating":80,"rcCntT":20,"ord1CntT":5,"ord2CntT":2,"ord3CntT":2,"rcCntY":8,"ord1CntY":3,"ord2CntY":1,"ord3CntY":1,"chaksunY":100000000}),
        normalize_entry({"meet":"서울","rcDate":"20260822","rcNo":7,"hrNo":"2","hrName":"B","rating":60,"rcCntT":20,"ord1CntT":1,"ord2CntT":2,"ord3CntT":2,"rcCntY":8,"ord1CntY":1,"ord2CntY":1,"ord3CntY":1,"chaksunY":30000000}),
    ]
    result = analyze_entries(rows)
    assert abs(sum(h.model_probability for h in result.horses) - 1.0) < 1e-5
    assert result.horses[0].horse_name == "A"
