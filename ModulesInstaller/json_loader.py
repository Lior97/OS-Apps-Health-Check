import json

def load_json(file_path: str):
    with open(file_path) as f:
        return json.load(f)

def load_app_config(name: str) -> dict:
    ws_dir = "/jenkins/workspace/DevOps/Public-Images/Installer/Installer-Trigger/installer-os-monitoring"
    config_file = f"{ws_dir}/apps_services.json"
    config = load_json(config_file)
    return next((app for app in config.get("os", {}).get("applications", []) if app["name"] == name), dict())

