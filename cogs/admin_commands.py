"""
Commandes administratives du bot.
Ce module contient les commandes réservées aux administrateurs.
"""
import discord
from discord.ext import commands
from discord import app_commands

class AdminCommands(commands.Cog):
    """Commandes réservées aux administrateurs du serveur."""

    def __init__(self, bot):
        """
        Initialise le cog AdminCommands.

        Args:
            bot: L'instance du bot Discord.
        """
        self.bot = bot

    # La vérification des permissions se fait maintenant par commande avec des décorateurs

    @app_commands.command(name="kick", description="Expulse un membre du serveur.")
    @app_commands.describe(member="Le membre à expulser.", reason="La raison de l'expulsion (optionnel).")
    @app_commands.checks.has_permissions(kick_members=True, administrator=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        """
        Expulse un membre du serveur.

        Args:
            interaction: L'interaction de la commande slash.
            member: Le membre à expulser.
            reason: La raison de l'expulsion (optionnel).
        """
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} a été expulsé du serveur.")

    @app_commands.command(name="ban", description="Bannit un membre du serveur.")
    @app_commands.describe(member="Le membre à bannir.", reason="La raison du bannissement (optionnel).")
    @app_commands.checks.has_permissions(ban_members=True, administrator=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        """
        Bannit un membre du serveur.

        Args:
            interaction: L'interaction de la commande slash.
            member: Le membre à bannir.
            reason: La raison du bannissement (optionnel).
        """
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} a été banni du serveur.")

# Fonction setup requise par discord.py pour charger le cog
async def setup(bot):
    """
    Charge le cog AdminCommands.

    Args:
        bot: L'instance du bot Discord.
    """
    await bot.add_cog(AdminCommands(bot))
