"""
Bot Discord principal.
Ce script est le point d'entrée du bot Discord.
"""
import discord
from discord.ext import commands
import asyncio
import logging
import config  # Votre config.py qui charge config.json

# Configuration du logging de base pour le bot
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING) # Réduire le bruit de discord.py, mettre INFO pour plus de détails
logger = logging.getLogger('main')
logger.setLevel(logging.INFO)

# Vérifier si le token est chargé
if not config.token:
    logger.critical("ERREUR CRITIQUE: Le token du bot n'est pas défini dans config.py ou config.json.")
    exit()

# Créer un bot avec tous les intents (ajustez si nécessaire pour la production)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config.config.get("prefix", "!"), # Utiliser un préfixe de config.json ou défaut
                   intents=intents,
                   help_command=None) # help_command=None car nous avons une commande /help personnalisée

@bot.event
async def on_ready():
    logger.info(f"Bot connecté en tant que {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"Préfixe des commandes (pour les commandes texte si utilisées): {bot.command_prefix}")
    logger.info(f"Nombre de serveurs: {len(bot.guilds)}")

    loaded_cogs = list(bot.cogs.keys())
    logger.info(f"Cogs chargés ({len(loaded_cogs)}): {', '.join(loaded_cogs)}")

    # Synchronisation des commandes slash après la connexion du bot
    logger.info("Synchronisation des commandes slash globales...")
    try:
        # Synchroniser les commandes globales.
        # Pour synchroniser pour une guilde spécifique: await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        synced = await bot.tree.sync()
        logger.info(f"Synchronisé {len(synced)} commandes slash globales.")
        for cmd in synced:
            logger.debug(f"  - Commande synchronisée: /{cmd.name} (ID: {cmd.id})")
    except discord.errors.Forbidden as e:
        logger.error(f"Erreur de synchronisation des commandes slash: Accès interdit (Forbidden). Assurez-vous que le bot a la permission 'applications.commands'. Erreur: {e}")
    except discord.app_commands.CommandSyncFailure as e:
         logger.error(f"Échec de la synchronisation de certaines commandes slash. Commandes échouées: {e.failed_commands}")
         logger.exception("Trace complète de l'erreur de synchronisation:")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la synchronisation des commandes slash: {type(e).__name__} - {e}")
        logger.exception("Trace complète de l'erreur de synchronisation:")

# Fonction asynchrone pour charger les cogs
async def load_all_cogs():
    logger.info("Début du chargement des cogs...")
    loaded_cogs_list = []
    for cog_name in config.cogs:
        try:
            await bot.load_extension(cog_name)
            logger.info(f"Cog chargé avec succès: {cog_name}")
            # Le nom réel du cog (nom de la classe) peut être différent du nom du fichier/module
            # Pour obtenir le nom de la classe, il faudrait introspecter bot.cogs après le chargement
        except commands.ExtensionNotFound:
            logger.error(f"Erreur de chargement: Cog {cog_name} non trouvé (fichier manquant ou faute de frappe).")
        except commands.ExtensionAlreadyLoaded:
            logger.warning(f"Avertissement: Cog {cog_name} déjà chargé.")
        except commands.NoEntryPointError:
            logger.error(f"Erreur de chargement: Cog {cog_name} n'a pas de fonction setup().")
        except commands.ExtensionFailed as e:
            # L'exception originale est dans e.__cause__
            original_exception = e.__cause__ if e.__cause__ else e
            logger.error(f"Erreur de chargement: Cog {cog_name} a échoué. Erreur originale: {type(original_exception).__name__}: {original_exception}")
            logger.exception(f"Trace complète de l'échec du chargement du cog {cog_name}:") # Loggue la stacktrace
        except Exception as e:
            logger.error(f"Erreur inattendue lors du chargement du cog {cog_name}: {type(e).__name__} - {e}")
            logger.exception("Trace complète de l'erreur de chargement du cog:")

    # Afficher les noms de classe des cogs réellement chargés
    actual_loaded_cogs = list(bot.cogs.keys())
    logger.info(f"Chargement des cogs terminé. {len(actual_loaded_cogs)} cogs réellement dans bot.cogs: {', '.join(actual_loaded_cogs)}")


# Fonction principale asynchrone
async def main():
    """Fonction principale asynchrone."""
    # Assigner owner_id/owner_ids pour @app_commands.checks.is_owner()
    if config.dev_id:
        if isinstance(config.dev_id, list) and len(config.dev_id) > 0 :
            bot.owner_ids = set(int(id_str) for id_str in config.dev_id) # Assurez-vous que les IDs sont des int
            logger.info(f"Propriétaires du bot (owner_ids) définis sur : {bot.owner_ids}")
        elif isinstance(config.dev_id, (str, int)): # Si c'est un seul ID
             bot.owner_id = int(config.dev_id)
             logger.info(f"Propriétaire du bot (owner_id) défini sur : {bot.owner_id}")
        else:
            logger.warning("dev_id dans config.json n'est pas dans un format attendu (liste d'IDs ou ID unique). @is_owner pourrait ne pas fonctionner.")
    else:
        logger.warning("Aucun dev_id trouvé dans config.json. @is_owner se basera sur le propriétaire de l'application Discord.")

    async with bot:
        await load_all_cogs()

        # La synchronisation des commandes slash est maintenant gérée dans l'événement on_ready
        # après que le bot soit complètement connecté

        await bot.start(config.token)

# Démarrer le bot
if __name__ == "__main__":
    # Créer le dossier cogs s'il n'existe pas (au cas où, bien que les fichiers soient déjà là)
    # if not os.path.exists("cogs"):
    #     os.makedirs("cogs")
    asyncio.run(main())