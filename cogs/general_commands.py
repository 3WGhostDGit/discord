"""
Commandes générales du bot.
Ce module contient les commandes générales et utilitaires du bot.
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
import ast  # Pour l'analyse de code
import io   # Pour capturer stdout
import contextlib # Pour redirect_stdout
import traceback # Pour les erreurs détaillées
import asyncio
import concurrent.futures # Pour ThreadPoolExecutor
import math # Exemple de module sûr
import datetime # Exemple de module sûr
import random # Exemple de module sûr

# Configuration du logger
logger = logging.getLogger('discord.general_commands')
logger.setLevel(logging.DEBUG) # Mettez INFO en production si DEBUG est trop verbeux

# --- Définitions pour l'analyse et l'exécution sécurisée ---

# Modules dont l'import direct est interdit
DISALLOWED_MODULES  = {
    'os', 'subprocess', 'sys', 'shutil', 'ctypes', 'socket', 'requests',
    'pickle', 'marshal', 'importlib', 'ptrace', 'fcntl', 'urllib',
    '_thread', 'threading', 'multiprocessing', 'asyncio' # Éviter la manipulation de l'event loop du bot
}

# Fonctions/builtins dont l'appel direct est interdit
DISALLOWED_BUILTINS_CALLS = {
    'eval', 'exec', 'open', '__import__', 'compile', 'input', 'exit', 'quit',
    'breakpoint', 'memoryview'
}

# Noms dont l'utilisation directe ou l'accès à des attributs est suspect
DISALLOWED_NAMES_ATTRIBUTES = {
    '__builtins__', '__class__', '__subclasses__', '__globals__', '__code__',
    '__mro__', '__bases__', '__dict__', 'system', 'remove', 'unlink', 'rmdir',
    'listdir', 'popen', 'call', 'run', 'getoutput', 'check_output', 'path',
    'start_new_thread', 'fork'
}

# Builtins autorisés dans l'environnement d'exécution
ALLOWED_BUILTINS = {
    'print': print, 'len': len, 'range': range, 'str': str, 'int': int, 'float': float,
    'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'bool': bool,
    'abs': abs, 'round': round, 'max': max, 'min': min, 'sum': sum,
    'True': True, 'False': False, 'None': None,
    'isinstance': isinstance, 'issubclass': issubclass, 'callable': callable,
    'repr': repr, 'ascii': ascii, 'format': format, 'hasattr': hasattr, # getattr est risqué
    'sorted': sorted, 'zip': zip, 'enumerate': enumerate, 'reversed': reversed,
    'all': all, 'any': any, 'map': map, 'filter': filter,
    # Exclus : eval, exec, open, input, __import__, etc.
    # ATTENTION: getattr peut être utilisé pour contourner certaines protections.
}

# Globals sûrs pour l'exécution
SAFE_GLOBALS = {
    "__builtins__": ALLOWED_BUILTINS,
    "math": math,
    "datetime": datetime,
    "random": random,
    # Vous pouvez ajouter ici d'autres modules/fonctions que vous jugez sûrs
    # "votre_fonction_utile": votre_fonction_utile,
}


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
        self.imported_modules_in_code = set() # Modules que le code essaie d'importer

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imported_modules_in_code.add(alias.name.split('.')[0]) # os.path -> os
            if alias.name.split('.')[0] in DISALLOWED_MODULES:
                self.violations.append(f"Import interdit du module : `{alias.name}`")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module: # peut être None pour `from . import x`
            self.imported_modules_in_code.add(node.module.split('.')[0])
            if node.module.split('.')[0] in DISALLOWED_MODULES:
                self.violations.append(f"Import interdit depuis le module : `{node.module}`")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name): # Appel direct ex: print(), eval()
            func_name = node.func.id
            if func_name in DISALLOWED_BUILTINS_CALLS:
                self.violations.append(f"Appel interdit à la fonction/built-in : `{func_name}`")
        elif isinstance(node.func, ast.Attribute): # Appel de méthode ex: os.system()
            # Tenter de reconstruire l'appel pour une meilleure détection
            # `value` est l'objet, `attr` est l'attribut (méthode)
            obj_name = ""
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id

            method_name = node.func.attr
            full_call_str = f"{obj_name}.{method_name}" if obj_name else method_name

            if obj_name in self.imported_modules_in_code and obj_name in DISALLOWED_MODULES:
                 self.violations.append(f"Appel à une méthode du module interdit `{obj_name}` : `{method_name}`")
            elif method_name in DISALLOWED_NAMES_ATTRIBUTES :
                 self.violations.append(f"Appel de méthode potentiellement dangereux : `{full_call_str}`")


        self.generic_visit(node)

    def visit_Name(self, node: ast.Name): # Utilisation de variables/noms
        if node.id in DISALLOWED_NAMES_ATTRIBUTES:
            self.violations.append(f"Utilisation du nom potentiellement dangereux : `{node.id}`")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute): # Accès à des attributs ex: foo.bar
        # node.value est l'objet, node.attr est l'attribut
        attr_name = node.attr
        obj_name = ""
        if isinstance(node.value, ast.Name):
            obj_name = node.value.id

        if attr_name in DISALLOWED_NAMES_ATTRIBUTES:
            self.violations.append(f"Accès à l'attribut potentiellement dangereux : `.{attr_name}`")

        if obj_name in self.imported_modules_in_code and obj_name in DISALLOWED_MODULES:
            self.violations.append(f"Accès à un attribut du module interdit `{obj_name}` : `.{attr_name}`")

        self.generic_visit(node)

# --- Fin des définitions ---


class GeneralCommands(commands.Cog):
    """Commandes générales et utilitaires du bot."""

    def __init__(self, bot):
        self.bot = bot
        logger.info(f"Cog GeneralCommands initialisé avec bot: {bot.user if bot.user else 'Non connecté'}")
        # ThreadPoolExecutor pour exécuter le code de manière non bloquante
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


    def cog_unload(self):
        # S'assurer que l'executor est arrêté proprement
        self.executor.shutdown(wait=True)

    async def _analyze_code_ast(self, code_string: str) -> tuple[bool, list[str]]:
        """Analyse le code avec AST pour détecter des patterns dangereux."""
        try:
            tree = ast.parse(code_string)
            analyzer = CodeAnalyzer()
            analyzer.visit(tree)
            if analyzer.violations:
                return False, analyzer.violations
            return True, []
        except SyntaxError as e:
            return False, [f"Erreur de syntaxe dans le code fourni : {e}"]
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'analyse AST : {e}")
            return False, ["Erreur interne lors de l'analyse du code."]

    def _execute_code_in_thread(self, code_to_run_compiled, custom_globals, output_buffer):
        """Fonction exécutée dans le thread."""
        try:
            with contextlib.redirect_stdout(output_buffer):
                exec(code_to_run_compiled, custom_globals)
            return output_buffer.getvalue(), None
        except Exception: # Capturer toutes les exceptions d'exécution
            # Renvoyer la trace complète dans la sortie standard (capturée)
            # et aussi dans le message d'erreur pour plus de clarté.
            tb_str = traceback.format_exc()
            print(f"\n--- ERREUR D'EXÉCUTION ---\n{tb_str}") # Sera capturé par redirect_stdout
            return output_buffer.getvalue(), tb_str


    @app_commands.command(name="ping", description="Commande simple pour tester si le bot répond.")
    async def ping(self, interaction: discord.Interaction):
        logger.debug(f"Commande /ping invoquée par {interaction.user} (ID: {interaction.user.id})")
        try:
            await interaction.response.send_message("Pong!")
            logger.info(f"Réponse 'Pong!' envoyée à {interaction.user}")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande /ping: {type(e).__name__} - {e}")
            try:
                await interaction.followup.send("Pong! (followup)")
                logger.info(f"Réponse 'Pong!' envoyée via followup à {interaction.user}")
            except Exception as e2:
                logger.error(f"Erreur lors de l'envoi du followup: {type(e2).__name__} - {e2}")

    @app_commands.command(name="hello", description="Salue l'utilisateur qui a invoqué la commande.")
    async def hello(self, interaction: discord.Interaction):
        logger.debug(f"Commande /hello invoquée par {interaction.user} (ID: {interaction.user.id})")
        try:
            await interaction.response.send_message(f"Bonjour, {interaction.user.mention}!")
            logger.info(f"Salutation envoyée à {interaction.user}")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande /hello: {type(e).__name__} - {e}")
            try:
                await interaction.followup.send(f"Bonjour, {interaction.user.mention}! (followup)")
                logger.info(f"Salutation envoyée via followup à {interaction.user}")
            except Exception as e2:
                logger.error(f"Erreur lors de l'envoi du followup: {type(e2).__name__} - {e2}")

    @app_commands.command(name="say", description="Fait répéter un message par le bot.")
    @app_commands.describe(message="Le message à répéter.")
    async def say(self, interaction: discord.Interaction, message: str):
        logger.debug(f"Commande /say invoquée par {interaction.user} (ID: {interaction.user.id}) avec message: {message}")
        try:
            await interaction.response.send_message(message)
            logger.info(f"Message répété pour {interaction.user}: {message[:50]}...")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande /say: {type(e).__name__} - {e}")
            try:
                await interaction.followup.send(message)
                logger.info(f"Message répété via followup pour {interaction.user}: {message[:50]}...")
            except Exception as e2:
                logger.error(f"Erreur lors de l'envoi du followup: {type(e2).__name__} - {e2}")

    # Fonction de vérification personnalisée pour le propriétaire
    async def is_bot_owner(self, interaction: discord.Interaction) -> bool:
        if self.bot.owner_id:
            return interaction.user.id == self.bot.owner_id
        if self.bot.owner_ids:
            return interaction.user.id in self.bot.owner_ids
        # Si aucun owner_id(s) n'est défini, essayez de récupérer le propriétaire de l'application
        # Cela peut être moins fiable si le bot est dans une équipe sans propriétaires explicitement définis.
        app_info = await self.bot.application_info()
        if app_info.team:
            return interaction.user.id in [member.id for member in app_info.team.members]
        return interaction.user.id == app_info.owner.id

    @app_commands.command(name="run", description="[DANGEREUX] Exécute du code Python (propriétaire du bot uniquement).")
    @app_commands.describe(code="Le bloc de code Python à exécuter.")
    # @app_commands.checks.is_owner() # <--- SUPPRIMEZ OU COMMENTEZ CETTE LIGNE
    async def run_python_code(self, interaction: discord.Interaction, code: str):
        """Exécute un bloc de code Python fourni par l'utilisateur."""

        # **CRUCIAL POUR LA SÉCURITÉ : Vérification du propriétaire ici**
        if not await self.is_bot_owner(interaction):
            await interaction.response.send_message(
                "❌ Désolé, cette commande est réservée au(x) propriétaire(s) du bot.",
                ephemeral=True
            )
            logger.warning(f"Tentative d'utilisation de /run par un non-propriétaire: {interaction.user} (ID: {interaction.user.id})")
            return

        await interaction.response.defer(ephemeral=False) # Réponse initiale, peut prendre du temps
        logger.info(f"Commande /run invoquée par {interaction.user} (propriétaire). Code: {code[:100]}...")

        # 1. Analyse statique du code
        is_safe, violations = await self._analyze_code_ast(code)
        if not is_safe:
            # Limiter la taille du code à afficher
            code_display = code
            if len(code_display) > 1000:
                code_display = code_display[:1000] + "\n... (code tronqué)"

            violations_str = "\n- ".join(violations)
            embed = discord.Embed(
                title="❌ Analyse du Code Échouée",
                color=discord.Color.red()
            )

            # Ajouter le code source
            embed.add_field(
                name="📝 Code Source",
                value=f"```py\n{code_display}\n```",
                inline=False
            )

            # Ajouter les violations
            embed.add_field(
                name="⚠️ Violations Détectées",
                value=f"Le code fourni contient des éléments potentiellement dangereux ou des erreurs:\n- {violations_str}",
                inline=False
            )

            await interaction.followup.send(embed=embed)
            return

        # 2. Compilation (rapide vérification de syntaxe supplémentaire)
        try:
            compiled_code = compile(code, '<discord_run_command>', 'exec')
        except SyntaxError as e:
            # Limiter la taille du code à afficher
            code_display = code
            if len(code_display) > 1000:
                code_display = code_display[:1000] + "\n... (code tronqué)"

            embed = discord.Embed(
                title="❌ Erreur de Syntaxe",
                color=discord.Color.red()
            )

            # Ajouter le code source
            embed.add_field(
                name="📝 Code Source",
                value=f"```py\n{code_display}\n```",
                inline=False
            )

            # Ajouter l'erreur de syntaxe
            embed.add_field(
                name="⚠️ Erreur de Syntaxe",
                value=f"```py\n{e}\n```",
                inline=False
            )

            await interaction.followup.send(embed=embed)
            return

        # 3. Exécution du code dans un thread séparé
        output_buffer = io.StringIO()
        custom_globals = SAFE_GLOBALS.copy()

        try:
            # Exécuter le code dans un thread pour éviter de bloquer la boucle d'événements
            future = self.bot.loop.run_in_executor(
                self.executor,
                self._execute_code_in_thread,
                compiled_code,
                custom_globals,
                output_buffer
            )

            # Attendre le résultat avec timeout
            output, error = await asyncio.wait_for(future, timeout=5.0)

            # Préparer la réponse
            if output:
                # Limiter la taille de la sortie
                if len(output) > 1900:
                    output = output[:1900] + "\n... (sortie tronquée)"

                # Limiter la taille du code à afficher
                code_display = code
                if len(code_display) > 1000:
                    code_display = code_display[:1000] + "\n... (code tronqué)"

                embed = discord.Embed(
                    title="✅ Code Exécuté",
                    color=discord.Color.green()
                )

                # Ajouter le code source
                embed.add_field(
                    name="📝 Code Source",
                    value=f"```py\n{code_display}\n```",
                    inline=False
                )

                # Ajouter le résultat
                embed.add_field(
                    name="🔍 Résultat",
                    value=f"```py\n{output}\n```",
                    inline=False
                )

                if error:
                    embed.add_field(
                        name="⚠️ Erreur d'exécution",
                        value=f"```py\n{error[:1000]}\n```",
                        inline=False
                    )
                    embed.color = discord.Color.gold()
            else:
                # Limiter la taille du code à afficher
                code_display = code
                if len(code_display) > 1000:
                    code_display = code_display[:1000] + "\n... (code tronqué)"

                embed = discord.Embed(
                    title="✅ Code Exécuté",
                    color=discord.Color.green()
                )

                # Ajouter le code source
                embed.add_field(
                    name="📝 Code Source",
                    value=f"```py\n{code_display}\n```",
                    inline=False
                )

                # Ajouter le résultat
                embed.add_field(
                    name="🔍 Résultat",
                    value="Le code a été exécuté sans sortie.",
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except asyncio.TimeoutError:
            # Limiter la taille du code à afficher
            code_display = code
            if len(code_display) > 1000:
                code_display = code_display[:1000] + "\n... (code tronqué)"

            embed = discord.Embed(
                title="⏱️ Timeout",
                description="L'exécution du code a pris trop de temps et a été interrompue.",
                color=discord.Color.red()
            )

            # Ajouter le code source
            embed.add_field(
                name="📝 Code Source",
                value=f"```py\n{code_display}\n```",
                inline=False
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'exécution du code: {e}")

            # Limiter la taille du code à afficher
            code_display = code
            if len(code_display) > 1000:
                code_display = code_display[:1000] + "\n... (code tronqué)"

            embed = discord.Embed(
                title="❌ Erreur Inattendue",
                color=discord.Color.red()
            )

            # Ajouter le code source
            embed.add_field(
                name="📝 Code Source",
                value=f"```py\n{code_display}\n```",
                inline=False
            )

            # Ajouter l'erreur
            embed.add_field(
                name="⚠️ Erreur",
                value=f"```py\n{traceback.format_exc()[:1500]}\n```",
                inline=False
            )

            await interaction.followup.send(embed=embed)


async def setup(bot):
    """Fonction d'installation du cog, appelée par bot.load_extension()."""
    await bot.add_cog(GeneralCommands(bot))
    logger.info("Cog GeneralCommands chargé avec succès.")