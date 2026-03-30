import os
import asyncio
import discord

from .client import discordClient
from .log import logger
from .tools.memory import add_memory, _load, _save

# typing
from discord import Message


def resolve_mentions(message: Message) -> str:
    content = message.content
    for user in message.mentions:
        display = f"@USER[{user.name}]"
        content = content.replace(f"<@{user.id}>", display)
        content = content.replace(f"<@!{user.id}>", display)
    for channel in message.channel_mentions:
        content = content.replace(f"<#{channel.id}>", f"#{channel.name}")
    for role in message.role_mentions:
        content = content.replace(f"<@&{role.id}>", f"@ROLE[{role.name}]")
    return content


def format_author(author) -> str:
    if author.display_name != author.name:
        return f"{author.name} ({author.display_name})"
    return author.name


def run_discord_bot():
    @discordClient.event
    async def on_ready():
        await discordClient.tree.sync()
        loop = asyncio.get_event_loop()
        loop.create_task(discordClient.process_messages())
        logger.info(f'{discordClient.user} is now running!')

    @discordClient.tree.command(name="chat", description="Have a chat with the bot")
    async def chat(interaction: discord.Interaction, *, message: str):
        if discordClient.is_replying_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **WARN: You already on replyAll mode. If you want to use the Slash Command, switch to normal mode by using `/replyall` again**")
            logger.warning(
                "\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == discordClient.user:
            return
        username = str(interaction.user)
        discordClient.current_channel = interaction.channel
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /chat [{message}] in ({discordClient.current_channel})")

        attributed_message = f"{format_author(interaction.user)}: {message}"
        await discordClient.enqueue_message(interaction, attributed_message)

    @discordClient.tree.command(name="private", description="Toggle private access")
    async def private(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not discordClient.isPrivate:
            discordClient.isPrivate = not discordClient.isPrivate
            logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
            await interaction.followup.send(
                "> **INFO: Next, the response will be sent via private reply. If you want to switch back to public mode, use `/public`**")
        else:
            logger.info("You already on private mode!")
            await interaction.followup.send(
                "> **WARN: You already on private mode. If you want to switch to public mode, use `/public`**")

    @discordClient.tree.command(name="public", description="Toggle public access")
    async def public(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if discordClient.isPrivate:
            discordClient.isPrivate = not discordClient.isPrivate
            await interaction.followup.send(
                "> **INFO: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**")
            logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
        else:
            await interaction.followup.send(
                "> **WARN: You already on public mode. If you want to switch to private mode, use `/private`**")
            logger.info("You already on public mode!")

    @discordClient.tree.command(name="replyall", description="Toggle replyAll access")
    async def replyall(interaction: discord.Interaction):
        discordClient.replying_all_discord_channel_id = str(
            interaction.channel_id)
        await interaction.response.defer(ephemeral=False)
        if discordClient.is_replying_all == "True":
            discordClient.is_replying_all = "False"
            await interaction.followup.send(
                "> **INFO: Next, the bot will response to the Slash Command. If you want to switch back to replyAll mode, use `/replyAll` again**")
            logger.warning("\x1b[31mSwitch to normal mode\x1b[0m")
        elif discordClient.is_replying_all == "False":
            discordClient.is_replying_all = "True"
            await interaction.followup.send(
                "> **INFO: Next, the bot will disable Slash Command and responding to all message in this channel only. If you want to switch back to normal mode, use `/replyAll` again**")
            logger.warning("\x1b[31mSwitch to replyAll mode\x1b[0m")

    @discordClient.tree.command(name="remember", description="Add a memory the bot will retain permanently")
    async def remember(interaction: discord.Interaction, memory: str):
        await interaction.response.defer(ephemeral=True)
        add_memory(memory)
        await interaction.followup.send(f"> **Remembered:** {memory}")

    @discordClient.tree.command(name="memories", description="List all stored memories")
    async def memories(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        entries = _load()
        if not entries:
            await interaction.followup.send("> **No memories stored.**")
            return
        lines = "\n".join(f"{i+1}. {m['content']}" for i, m in enumerate(entries))
        await interaction.followup.send(f"> **Memories:**\n{lines}")

    @discordClient.tree.command(name="forget", description="Remove a memory by its number (use /memories to list)")
    async def forget(interaction: discord.Interaction, index: int):
        await interaction.response.defer(ephemeral=True)
        entries = _load()
        if index < 1 or index > len(entries):
            await interaction.followup.send(f"> **Error: No memory at index {index}.**")
            return
        removed = entries.pop(index - 1)
        _save(entries)
        await interaction.followup.send(f"> **Forgot:** {removed['content']}")

    @discordClient.tree.command(name="reset", description="Clear conversation history")
    async def reset(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        discordClient.conversation_history = []
        await interaction.followup.send("> **INFO: I have forgotten everything.**")
        logger.warning(
            f"\x1b[31m{discordClient.chatModel} bot has been successfully reset\x1b[0m")

    @discordClient.tree.command(name="help", description="Show help for the bot")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":star: **COMMANDS**
        - `/chat [message]` Chat with the bot
        - `/private` Switch to private mode
        - `/public` Switch to public mode
        - `/replyall` Toggle replyAll mode (bot responds to all messages in this channel)
        - `/reset` Clear conversation history
        - `/remember [memory]` Add a memory the bot permanently retains
        - `/memories` List all stored memories
        - `/forget [index]` Remove a memory by index""")
        logger.info("\x1b[31mSomeone needs help!\x1b[0m")

    @discordClient.event
    async def on_message(message):
        if discordClient.is_replying_all == "True":
            if message.author == discordClient.user:
                return
            if discordClient.replying_all_discord_channel_id:
                if message.channel.id == int(discordClient.replying_all_discord_channel_id):
                    username = str(message.author)
                    attachments = message.attachments
                    att_placeholders = "".join(
                        f" [Attachment {i+1}: {a.filename}]" for i, a in enumerate(attachments)
                    )
                    user_message = f"{format_author(message.author)}: {resolve_mentions(message)}{att_placeholders}"
                    discordClient.current_channel = message.channel
                    logger.info(
                        f"\x1b[31m{username}\x1b[0m : '{message.content}' ({discordClient.current_channel})")

                    await discordClient.enqueue_batch_message(message, user_message, attachments)
            else:
                logger.exception(
                    "replying_all_discord_channel_id not found, please use the command `/replyall` again.")

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    discordClient.run(TOKEN)
