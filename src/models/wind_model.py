from xgboost import XGBRegressor

def get_wind_model():
    model = XGBRegressor(
        n_estimators = 200,
        learning_rate = 0.05,
        max_depth = 6,
        tree_method ="hist",
        random_state = 42
    )

    return model