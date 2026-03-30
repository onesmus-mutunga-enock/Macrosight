from apps.ml.services.feature_mapper import map_features_to_array


def test_map_features_to_array_basic():
    features = {'a': 1, 'b': 2}
    arr = map_features_to_array(features, ['a', 'b'])
    assert arr.shape == (1, 2)
    assert arr[0, 0] == 1.0
    assert arr[0, 1] == 2.0
