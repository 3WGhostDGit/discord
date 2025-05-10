"""
Configuration du bot Discord.
Ce fichier contient les paramètres de configuration du bot.
"""
import json
import os

# Charger la configuration depuis le fichier config.json
def load_config():
    """Charge la configuration depuis le fichier config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERREUR: Le fichier config.json n'a pas été trouvé.")
        return None
    except json.JSONDecodeError:
        print("ERREUR: Le fichier config.json contient des erreurs de syntaxe JSON.")
        return None

# Charger la configuration
config = load_config()

# Token du bot
token = config.get('token') if config else None

# Liste des cogs à charger
cogs = [
    'cogs.general_commands',
    'cogs.admin_commands',
    'cogs.info_commands',
    'cogs.functionality_bot'  # Ajout du nouveau cog pour AntiGhostPing
]

# IDs des canaux de statut
status_channel_ids = config.get('status_channel_ids', []) if config else []

# IDs des développeurs
dev_id = config.get('dev_id', []) if config else []
