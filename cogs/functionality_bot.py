"""
Fonctionnalités diverses du bot, incluant AntiGhostPing.
"""
import discord
from discord.ext import commands
from discord import AuditLogAction, Colour, Embed, Message
import logging
import datetime # Pour le timestamp dans le footer

# Configuration du logger pour ce cog
logger = logging.getLogger('discord.functionality_bot')
# Configuration du handler si nécessaire
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class AntiGhostPingCog(commands.Cog, name="AntiGhostPing"):
    """
    Détecte et signale les ghost pings avec style.
    Un ghost ping se produit lorsqu'un utilisateur mentionne quelqu'un puis supprime rapidement le message.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("Cog AntiGhostPing [Stylé] initialisé.")

    @commands.Cog.listener()
    async def on_message_delete(self, message: Message):
        # Log de base pour le débogage
        # logger.info(f"Message supprimé (ID: {message.id}) par {message.author} dans {message.channel.name}. Contenu: '{message.content}'")

        # 1. Ignorer les messages hors des serveurs (DMs)
        if not message.guild:
            return

        # 2. Ignorer si le message ne contenait aucune mention
        if not message.mentions:
            return

        # 3. Ignorer si l'auteur est un bot
        if message.author.bot:
            return

        # 4. Ignorer si l'auteur a la permission de gérer les messages
        if isinstance(message.author, discord.Member) and \
           message.author.guild_permissions.manage_messages:
            logger.debug(f"AntiGhostPing: Ignoré (auteur {message.author.name} a manage_messages)")
            return

        # 5. Logique pour les mentions uniques (auto-mention, mention de bot unique)
        if len(message.mentions) == 1:
            first_mention = message.mentions[0]
            if first_mention == message.author:  # Auto-mention unique
                logger.debug(f"AntiGhostPing: Ignoré (auto-mention unique par {message.author.name})")
                return
            if first_mention.bot:  # Mention de bot unique (si la cible est un bot)
                logger.debug(f"AntiGhostPing: Ignoré (mention unique d'un bot par {message.author.name})")
                return
        
        # 6. Vérification par log d'audit : le message a-t-il été supprimé par quelqu'un d'autre ?
        try:
            if message.guild.me.guild_permissions.view_audit_log:
                async for entry in message.guild.audit_logs(limit=1, action=AuditLogAction.message_delete):
                    # Vérifier si l'utilisateur qui a supprimé est différent de l'auteur du message
                    # et si la cible de la suppression est bien l'auteur du message (plus précis)
                    if entry.user and entry.user.id != message.author.id and entry.target == message.author:
                        # On pourrait ajouter un check sur l'ID du message si disponible dans l'entry,
                        # mais c'est souvent non fiable pour les suppressions rapides.
                        # entry.extra.channel == message.channel et entry.extra.count >= 1
                        logger.debug(f"AntiGhostPing: Ignoré (log d'audit indique suppression par {entry.user.name} != auteur {message.author.name})")
                        return
            else:
                logger.warning(f"AntiGhostPing [{message.guild.name}]: Permission 'View Audit Log' manquante.")
        except discord.Forbidden:
            logger.warning(f"AntiGhostPing [{message.guild.name}]: Accès interdit aux logs d'audit.")
        except Exception as e:
            logger.error(f"AntiGhostPing [{message.guild.name}]: Erreur lors de la vérification du log d'audit: {type(e).__name__} - {e}")

        # Si on arrive ici, c'est un ghost ping potentiel
        logger.info(f"AntiGhostPing: Ghost ping potentiel détecté de {message.author.name} dans {message.channel.name}")

        # Préparation du contenu du message pour l'embed
        message_content_display = message.content
        if not message_content_display:
            if message.embeds:
                message_content_display = f"[Contenait {len(message.embeds)} embed(s) - Non affichable]"
            elif message.attachments:
                message_content_display = f"[Contenait {len(message.attachments)} fichier(s) joint(s)]"
            else:
                message_content_display = "[Contenu vide ou éphémère]"
        
        # Limiter la longueur du contenu affiché pour éviter des embeds trop longs
        max_content_length = 1000
        if len(message_content_display) > max_content_length:
            message_content_display = message_content_display[:max_content_length] + "..."


        # Création de l'embed stylé
        embed_color = discord.Color.from_rgb(0, 255, 255) # Cyan électrique

        embed = Embed(
            # title="👻 GHOST PING DETECTED 📡",
            color=embed_color,
            timestamp=message.created_at # Utilise le timestamp de création du message original
        )
        
        embed.set_author(name="🚨 ALERTE GHOST PING // TRANSMISSION INTERCEPTÉE 🚨", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        if message.author.avatar:
            embed.set_thumbnail(url=message.author.avatar.url)

        embed.add_field(
            name=f"🕵️‍♂️ Auteur du ping {message.author.name} :",
            value=f"{message.author.mention} (`{message.author.name}#{message.author.discriminator}`)",
            inline=False
        )
        embed.add_field(
            name="💬 Qu'est ce que tu caches ?🤦‍♀️ :",
            value=f"```\n{discord.utils.escape_markdown(message_content_display)}\n```",
            inline=False
        )
        embed.add_field(
            name="📍 Zone d'Impact:",
            value=f"{message.channel.mention} (Canal: `{message.channel.name}`)",
            inline=False
        )
        
        # Informations sur les mentions spécifiques (si plus d'une ou pas l'auteur)
        mentioned_users = [m.mention for m in message.mentions if m != message.author and not m.bot]
        if mentioned_users:
            embed.add_field(
                name="🎯 Cible(s) du Ping Fantôme:",
                value=", ".join(mentioned_users),
                inline=False
            )

        embed.set_footer(
            text=f"Système de détection v2.1 | ID Auteur: {message.author.id}",
            icon_url="https://cdn.discordapp.com/emojis/797907288890671104.png?v=1" # Un emoji de radar ou tech
        )


        try:
            await message.channel.send(embed=embed)
            logger.info(f"AntiGhostPing: Embed stylé envoyé pour {message.author.name} dans {message.channel.name}.")
        except discord.Forbidden:
            logger.warning(f"AntiGhostPing: Impossible d'envoyer l'embed stylé dans {message.channel.name} (permissions manquantes).")
        except Exception as e:
            logger.error(f"AntiGhostPing: Erreur lors de l'envoi de l'embed stylé: {type(e).__name__} - {e}")


async def setup(bot: commands.Bot):
    """
    Charge le cog AntiGhostPing (version stylée).

    Args:
        bot: L'instance du bot Discord.
    """
    await bot.add_cog(AntiGhostPingCog(bot))
    logger.info("Cog AntiGhostPing [Stylé] chargé avec succès.")