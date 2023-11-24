cmip6_activities = ["CMIP", "ScenarioMIP"]


def experiment_to_activity(experiment: str) -> str:
    if experiment == "historical":
        return "CMIP"
    elif experiment in ["ssp245", "ssp370", "ssp585", "ssp126"]:
        return "ScenarioMIP"
    else:
        raise ValueError(f"Unknown experiment: {experiment}")
