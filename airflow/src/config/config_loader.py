import json
import os

# Get the path to the JSON file
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_task_config():
    """Reads task configuration from JSON file."""
    try:
        with open(CONFIG_PATH, "r") as file:
            config = json.load(file)
        return config.get("tasks", [])
    except Exception as e:
        raise RuntimeError(f"Error loading configuration: {e}")
