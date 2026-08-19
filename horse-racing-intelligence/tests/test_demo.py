from backend.app.services.demo import ranking


def test_demo_probabilities_are_valid():
    race = ranking()
    assert race.horses
    assert all(0 <= h.model_probability <= 1 for h in race.horses)
    assert race.horses[0].model_probability >= race.horses[-1].model_probability
