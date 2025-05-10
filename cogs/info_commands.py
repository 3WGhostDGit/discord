"""
Commandes d'information du bot.
Ce module contient les commandes fournissant des informations sur le serveur, les utilisateurs, etc.
ET la commande d'aide générale.
"""
import discord
from discord.ext import commands
from discord import app_commands, Embed, Color
import datetime
from collections import defaultdict # Pour grouper les commandes par cog
import logging # Ajout du logger

logger = logging.getLogger('discord.info_commands') # Logger spécifique au cog

class InfoCommands(commands.Cog):
    """Commandes fournissant des informations et la commande d'aide."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("Cog InfoCommands initialisé.") # Log d'initialisation

    # ... (vos commandes serverinfo, userinfo, botinfo restent les mêmes,
    #      j'ai juste ajouté le logger.info dans __init__ et importé logging)
    # Vous pouvez les améliorer comme suggéré dans la réponse précédente avec format_dt etc. si vous le souhaitez.

    @app_commands.command(name="serverinfo", description="Affiche des informations sur le serveur.")
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Cette commande ne peut être utilisée que sur un serveur.", ephemeral=True)
            return

        embed = Embed(
            title=f"⚙️ Informations sur {guild.name}",
            description=guild.description if guild.description else "Aucune description de serveur.",
            color=Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="👑 Propriétaire", value=guild.owner.mention if guild.owner else "Inconnu", inline=True)
        embed.add_field(name="🆔 ID du Serveur", value=guild.id, inline=True)
        embed.add_field(name="📅 Créé le", value=discord.utils.format_dt(guild.created_at, style='D'), inline=True)
        embed.add_field(name="👥 Membres", value=str(guild.member_count), inline=True)
        embed.add_field(name="💬 Canaux", value=str(len(guild.text_channels) + len(guild.voice_channels)), inline=True)
        embed.add_field(name="🏷️ Rôles", value=str(len(guild.roles)), inline=True)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Affiche des informations sur un utilisateur.")
    @app_commands.describe(member="Le membre dont on veut les informations (par défaut: vous-même).")
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        target_member = member or interaction.user

        embed = Embed(
            title=f"👤 Informations sur {target_member.display_name}",
            color=target_member.color if target_member.color != Color.default() else Color.light_grey(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=target_member.display_avatar.url if target_member.display_avatar else None)
        embed.add_field(name="📛 Nom complet", value=f"{target_member}", inline=True) # Utilise __str__ qui inclut le discr.
        embed.add_field(name="🆔 ID Utilisateur", value=target_member.id, inline=True)
        embed.add_field(name="✏️ Surnom", value=target_member.nick or "Aucun", inline=True)
        embed.add_field(name="📅 Compte créé le", value=discord.utils.format_dt(target_member.created_at, style='R'), inline=True)
        if isinstance(target_member, discord.Member) and target_member.joined_at:
             embed.add_field(name="👋 A rejoint le serveur le", value=discord.utils.format_dt(target_member.joined_at, style='R'), inline=True)
        embed.add_field(name="⭐ Rôle principal", value=target_member.top_role.mention if isinstance(target_member, discord.Member) else "N/A", inline=True)
        if isinstance(target_member, discord.Member):
            roles = [role.mention for role in reversed(target_member.roles) if not role.is_default()]
            roles_str = ", ".join(roles) if roles else "Aucun rôle spécifique."
            if len(roles_str) > 1020:
                roles_str = roles_str[:1020] + "..."
            embed.add_field(name=f"🛡️ Rôles ({len(roles)})", value=roles_str, inline=False)

        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="Affiche des informations sur le bot.")
    async def display_bot_info(self, interaction: discord.Interaction):
        bot_user = self.bot.user

        embed = Embed(
            title=f"🤖 Informations sur {bot_user.name}",
            description=f"Un bot Discord utile et performant !",
            color=Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if bot_user.avatar:
            embed.set_thumbnail(url=bot_user.avatar.url)

        # Lire le dev_id depuis la config pour l'afficher si c'est pertinent
        dev_mention = "Non spécifié"
        if self.bot.owner_id:
            try:
                owner = await self.bot.fetch_user(self.bot.owner_id)
                dev_mention = owner.mention
            except discord.NotFound:
                dev_mention = f"ID: {self.bot.owner_id} (utilisateur non trouvé)"
        elif self.bot.owner_ids:
            owners_mentions = []
            for owner_id_val in self.bot.owner_ids:
                try:
                    owner = await self.bot.fetch_user(owner_id_val)
                    owners_mentions.append(owner.mention)
                except discord.NotFound:
                     owners_mentions.append(f"ID: {owner_id_val} (non trouvé)")
            dev_mention = ", ".join(owners_mentions) if owners_mentions else "Non spécifié"


        embed.add_field(name=" डेवलपeur(s)", value=dev_mention, inline=True)
        embed.add_field(name="🏷️ Version", value="1.0.1", inline=True)
        embed.add_field(name="⚙️ Librairie", value=f"discord.py v{discord.__version__}", inline=True)
        embed.add_field(name="📅 Créé le", value=discord.utils.format_dt(bot_user.created_at, style='D'), inline=True)
        embed.add_field(name="🌍 Serveurs", value=str(len(self.bot.guilds)), inline=True)

        # Calcul des utilisateurs plus robuste
        total_users = 0
        try: # Pourrait échouer si les intents de membres ne sont pas activés partout
            total_users = sum(g.member_count for g in self.bot.guilds if g.member_count is not None)
        except AttributeError: # Si guild.member_count n'est pas disponible
            total_users = "N/A (Intents manquants?)"

        embed.add_field(name="👥 Utilisateurs (estimé)", value=str(total_users), inline=True)
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="help", description="Affiche de l'aide sur les commandes du bot.")
    @app_commands.describe(command_name="Le nom de la commande pour laquelle afficher l'aide (optionnel).")
    async def help_command(self, interaction: discord.Interaction, command_name: str = None):
        """Affiche une liste de toutes les commandes slash ou des détails sur une commande spécifique."""

        # DEFER EST IMPORTANT, surtout si la recherche de commande peut prendre du temps.
        # Si command_name est fourni, on pourrait faire une recherche, donc defer.
        # Si pas de command_name, la construction de la liste peut aussi prendre un peu de temps.
        # On peut rendre éphémère si on s'attend à des erreurs, sinon non.
        await interaction.response.defer(ephemeral=False) # Modifié pour ne pas être éphémère par défaut

        bot_user = self.bot.user
        embed_color = Color.blurple()

        if command_name:
            cmd_to_find_str = command_name.lower().strip().replace("/", "") # Nettoyer le nom
            found_cmd: app_commands.Command | app_commands.Group = None

            # Rechercher dans toutes les commandes enregistrées (globales et de guilde)
            # bot.tree.walk_commands() est excellent pour cela.
            for cmd_obj in self.bot.tree.walk_commands():
                # Pour les sous-commandes, qualified_name est 'group subcommand'
                # Pour les commandes simples, qualified_name est 'command'
                if cmd_obj.qualified_name == cmd_to_find_str:
                    found_cmd = cmd_obj
                    break
                # Si ce n'est pas une correspondance exacte et que l'utilisateur n'a pas mis le nom du groupe
                # pour une sous-commande, on pourrait essayer de le trouver.
                # Exemple: /help clear au lieu de /help admin clear
                if isinstance(cmd_obj.parent, app_commands.Group) and cmd_obj.name == cmd_to_find_str:
                    # Prudence ici, peut mener à des ambiguïtés si 'clear' existe en global et en sous-commande
                    # Pour l'instant, on priorise la correspondance exacte avec qualified_name
                    pass # On laisse la recherche par qualified_name gérer cela

            if not found_cmd:
                await interaction.followup.send( # Utiliser followup après defer
                    f"😕 Désolé, la commande `/{command_name}` n'a pas été trouvée ou n'est pas accessible.",
                    ephemeral=True
                )
                return

            embed = Embed(
                title=f"❓ Aide pour : `/{found_cmd.qualified_name}`",
                description=found_cmd.description or "Aucune description fournie.",
                color=embed_color,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            if bot_user and bot_user.avatar:
                embed.set_thumbnail(url=bot_user.avatar.url)

            usage = f"`/{found_cmd.qualified_name}`"
            if hasattr(found_cmd, 'parameters') and found_cmd.parameters:
                params_usage = []
                params_description_list = []
                for param in found_cmd.parameters:
                    param_type_name = param.type.name if hasattr(param.type, 'name') else str(param.type).split('.')[-1].lower()
                    required_text = "" if param.required else " (Optionnel)" # "Requis" est implicite sans ça
                    param_name_formatted = f"<{param.name}>" if param.required else f"[{param.name}]"
                    params_usage.append(param_name_formatted)

                    desc_line = f"**`{param.name}`** (`{param_type_name}`{required_text}):\n> {param.description or 'Pas de description.'}"
                    if param.choices:
                        choices_str = ", ".join([f"`{choice.name}` (`{choice.value}`)" for choice in param.choices])
                        desc_line += f"\n> *Choix possibles:* {choices_str}"
                    params_description_list.append(desc_line)

                usage += " " + " ".join(params_usage)
                embed.add_field(name="📝 Utilisation", value=usage, inline=False)
                if params_description_list: # S'assurer qu'il y a des descriptions à afficher
                    embed.add_field(
                        name="🔧 Paramètres",
                        value="\n\n".join(params_description_list),
                        inline=False
                    )
                else:
                    embed.add_field(name="🔧 Paramètres", value="Cette commande ne prend aucun paramètre.", inline=False)

            else: # Cas des groupes qui n'ont pas de "parameters" directement mais des sous-commandes
                embed.add_field(name="📝 Utilisation", value=usage, inline=False)
                if isinstance(found_cmd, app_commands.Group):
                    sub_cmds_list = [f"`/{sub.qualified_name}`: {sub.description or 'Pas de description.'}" for sub in found_cmd.commands]
                    if sub_cmds_list:
                         embed.add_field(name="Sous-commandes", value="\n".join(sub_cmds_list), inline=False)
                else:
                    embed.add_field(name="🔧 Paramètres", value="Cette commande ne prend aucun paramètre.", inline=False)

            if found_cmd.cog_name:
                 embed.add_field(name="📦 Module", value=found_cmd.cog_name, inline=True)

            embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
            await interaction.followup.send(embed=embed)

        else: # Afficher la liste de toutes les commandes
            embed = Embed(
                title=f"📜 Aide des Commandes de {bot_user.name if bot_user else 'ce Bot'}",
                description=f"Voici la liste des commandes slash disponibles.\nUtilisez `/help <nom_commande>` pour plus de détails.",
                color=embed_color,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            if bot_user and bot_user.avatar:
                embed.set_thumbnail(url=bot_user.avatar.url)

            cogs_commands = defaultdict(list)
            # Utiliser walk_commands pour obtenir une liste plate de toutes les commandes (y compris sous-commandes)
            # Mais pour l'affichage général, on veut souvent grouper par cog et afficher les commandes de haut niveau.

            # On récupère les commandes de premier niveau.
            # walk_commands itère sur tout, y compris les sous-commandes.
            # get_commands() sans argument ou avec guild=None retourne les commandes globales de haut niveau.
            # get_commands(guild=interaction.guild) retourne celles de la guilde.

            top_level_commands = set()
            top_level_commands.update(self.bot.tree.get_commands(guild=None))
            if interaction.guild:
                 top_level_commands.update(self.bot.tree.get_commands(guild=interaction.guild))

            sorted_commands = sorted(list(top_level_commands), key=lambda cmd: cmd.qualified_name)

            for cmd_obj in sorted_commands:
                cog_name = cmd_obj.cog_name if hasattr(cmd_obj, "cog_name") and cmd_obj.cog_name else "Autres Commandes"
                cmd_display = f"`/{cmd_obj.qualified_name}`: {cmd_obj.description or 'Pas de description.'}"

                # Si c'est un groupe, indiquer qu'il a des sous-commandes
                if isinstance(cmd_obj, app_commands.Group) and cmd_obj.commands:
                    cmd_display += f" (Groupe - {len(cmd_obj.commands)} sous-commande(s))"

                cogs_commands[cog_name].append(cmd_display)

            if not cogs_commands:
                embed.description += "\n\n😕 Aucune commande n'a été trouvée."
            else:
                for cog_name_sorted, cmd_list in sorted(cogs_commands.items()):
                    if cmd_list:
                        field_value = "\n".join(cmd_list)
                        if len(field_value) > 1024:
                            field_value = field_value[:1020] + "\n..."
                        embed.add_field(name=f"**{cog_name_sorted}**", value=field_value, inline=False)

            embed.set_footer(text=f"Demandé par {interaction.user.display_name} | Total: {len(sorted_commands)} commandes de haut niveau", icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCommands(bot))
    logger.info("Cog InfoCommands (avec /help amélioré) chargé avec succès.")