# Discord XP Bot

A simple Discord bot that tracks users activity in a server and rewards them with XP, allowing them to level up to higher Discord roles.


## Features
- Tracks user text and voice activity in a server (messages sent and time spent in voice channels)
- Rewards users with XP for their activity and automatically assigns them roles based on it
- Allows server admins to customize XP rates, role requirements, and channels to track
- Supports multiple servers with separate XP tracking and role assignments

## Installation
1. Clone the repository
2. Rename the `.env.sample` file to `.env`
3. Create a new Discord bot application at https://discord.com/developers/applications
    - In the "General Information" tab:
        - (Optional) Customize the app with a name and an app icon
        - Copy the `Application ID` and `Public Key` to the `.env` file
    - In the "Installation" tab:
        - Tick at least the `Guild Install` checkbox
        - Copy the install link and keep it for later
        - In default install settings, add `application.commands` and `bot` scopes with the `Manage Roles`, `Send Messages`, `Use Slash Commands` and the `View Channels`  permissions
    - In the "Bot" tab:
        - (Optional) Customize your bot with a name and profile picture
        - Reset and copy your bot token to the `.env` file
        - Give your bot the presence, server members and message content intents
4. Execute the setup script with `bash setup.sh`
    - Make sure the bot is running properly with `service discord_xp_bot status`
5. Invite the bot to your server using the install link
6. Set up the Discord permissions for the bot on the server so that the commands can only be used in the proper channels and by the user you want.
7. Setup the bot in your Discord server
    - First, define the mod role using `/config mod_role @<role>` with the owner of the server. You should now be able to use the rest of the commands with any user with the mod role.
    - Then, define the channels to track with `/config channel <add|rm|show>`. Make sure the bot is also able to see the channels you want to track, respecting the permissions of the bot role.
    - Define the roles to assign with `/config role <add|rm|show>`. The `xp_threshold` argument is the amount of xp needed to automatically grant the specified `role`. All the added roles should be lower than the bot's one in the server role hierarchy. They should also be non-mentionable and the bot's role should not have the "mention @everyone" permission.
    - Define the XP rates with `/config rate <text|voice>`. The first argument is the amount of XP given per message sent or per minute spent in a voice channel. For the xp given per text message, you can also configure the msg cooldown before xp is granted again (to avoid spamming) and a factor reducing the xp gained for each subsequent message in the same day, down to the defined minimum and only for user with more than the "rank xp threshold".
    - Check the full config with `/config show`
8. Enjoy the bot!
