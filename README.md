# Bot Discord Simplifié pour Étudiants

Ce projet est une version simplifiée du bot Discord Pixelbot, conçue spécialement pour les étudiants qui apprennent à développer des bots Discord avec Python.

## Structure du Projet

```
simplified/
├── cogs/                    # Modules de commandes
│   ├── __init__.py
│   ├── anti_ghost_ping.py   # Détection des ghost pings
│   ├── info_commands.py     # Commandes d'information
│   └── utility_commands.py  # Commandes utilitaires
├── config.py                # Gestion de la configuration
├── main.py                  # Point d'entrée principal
├── README.md                # Ce fichier
└── utils.py                 # Fonctions utilitaires
```

## Fonctionnalités

Le bot inclut plusieurs fonctionnalités utiles :

1. **Commandes d'information**
   - `/infos` : Informations sur le bot
   - `/ping` : Affiche la latence du bot
   - `/serveur` : Informations sur le serveur
   - `/membre` : Informations sur un membre
   - `/avatar` : Affiche l'avatar d'un membre

2. **Commandes utilitaires**
   - `/say` : Fait dire quelque chose au bot (admin)
   - `/dm` : Envoie un message privé à un utilisateur (admin)
   - `/embed` : Crée un message formaté
   - `/tirage_de_des` : Simule des lancers de dés
   - `/help` : Affiche la liste des commandes

3. **Anti-Ghost Ping**
   - Détecte lorsqu'un utilisateur mentionne quelqu'un puis supprime son message
   - Affiche un message d'alerte avec le contenu du message supprimé

## Comment ça marche

### Le fichier `main.py`

C'est le point d'entrée du bot. Il contient :
- La classe `PixelBot` qui hérite de `commands.Bot`
- Les événements principaux comme `on_ready`
- La tâche de changement d'activité
- La gestion des erreurs

### Les Cogs

Les cogs sont des modules qui regroupent des commandes liées. Ils permettent d'organiser le code de manière logique :

1. **anti_ghost_ping.py** : Détecte les mentions supprimées
2. **info_commands.py** : Commandes d'information
3. **utility_commands.py** : Commandes utilitaires

### Les Utilitaires

Le fichier `utils.py` contient des fonctions réutilisables comme :
- `creer_embed` : Crée un embed Discord
- `formater_liste_roles` : Formate une liste de rôles pour l'affichage
- `obtenir_emoji_status` : Détermine l'emoji de statut d'un membre

### La Configuration

Le fichier `config.py` gère le chargement de la configuration depuis un fichier JSON ou des variables d'environnement.

## Installation et Utilisation

1. **Prérequis**
   - Python 3.8 ou supérieur
   - Bibliothèque py-cord (fork de discord.py)
   - pygit2 (pour les fonctionnalités Git)
   - rich (pour l'affichage amélioré dans le terminal)

2. **Installation**
   ```sh
   # Cloner le dépôt
   git clone https://github.com/start-from-scratch/discord.git
   cd discord

   # Installer les dépendances
   pip install -r requirements.txt
   ```

3. **Configuration**
   - Créez un fichier `config.json` à la racine du projet :
   ```json
   {
       "token": "VOTRE_TOKEN_DISCORD",
       "status_channel_ids": [],
       "dev_id": []
   }
   ```

4. **Lancement**
   ```sh
   python simplified/main.py
   ```

## Personnalisation

### Ajouter une nouvelle commande

1. Ouvrez le fichier du cog approprié (ou créez-en un nouveau)
2. Ajoutez votre commande en suivant ce modèle :

```python
@commands.slash_command(
    name="ma_commande",
    description="Description de ma commande"
)
async def ma_commande(self, ctx, parametre: Option(str, description="Description du paramètre")):
    # Votre code ici
    await ctx.respond("Réponse de la commande")
```

### Ajouter un nouvel événement

Dans le fichier du cog approprié :

```python
@commands.Cog.listener()
async def on_message(self, message):
    # Votre code ici
    if message.content == "Bonjour":
        await message.channel.send("Bonjour !")
```

## Ressources pour Apprendre

- [Documentation de py-cord](https://docs.pycord.dev/en/master/)
- [Guide des commandes slash](https://docs.pycord.dev/en/master/api/application_commands.html)
- [Guide des embeds](https://docs.pycord.dev/en/master/api/embed.html)
- [Documentation de pygit2](https://www.pygit2.org/)

## Conseils pour les Étudiants

1. **Commencez petit** : Comprenez d'abord les bases avant d'ajouter des fonctionnalités complexes
2. **Lisez la documentation** : La documentation de discord.py est très complète
3. **Expérimentez** : N'hésitez pas à modifier le code pour voir ce qui se passe
4. **Utilisez les commentaires** : Le code est abondamment commenté pour vous aider à comprendre

## Licence

Voir le fichier LICENCE dans le dépôt principal.
