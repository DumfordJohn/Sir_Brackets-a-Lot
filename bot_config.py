import json
import os

CONFIG_FILE = "bot_config.json"

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)
    
def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_guild_config(guild_id:int) -> dict:
    config = load_config()
    return config.get(str(guild_id), {})

def set_guild_config(guild_id: int, data: dict):
    config = load_config()
    config[str(guild_id)] = data
    save_config(config)