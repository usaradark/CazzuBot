'''
For all ongoing events that need to be monitored
'''

import xml.etree.ElementTree as ET
import html
import discord
from discord.ext import commands
from cogs.helper import HelperCog
AllEmoji = HelperCog.AllEmoji
import modules.utility

class AutomationsCog():
    def __init__(self, bot):
        self.bot = bot

    async def on_raw_reaction_add(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # Userauth
        try:
            userauth = tree.find('userauth')
            xml_role = userauth.find('role')
            guild = self.bot.get_guild(payload.guild_id)
            role = discord.utils.get(guild.roles, id=int(xml_role.find('id').text))
            xml_message = userauth.find('message')
            xml_emoji = userauth.find('emoji')

            if payload.message_id == int(xml_message.find('id').text):
                if str(payload.emoji) == html.unescape(xml_emoji.find('id').text):
                    await guild.get_member(payload.user_id)\
                                .add_roles(role)
        except ValueError:
            pass

        if payload.user_id == self.bot.user.id:
            return # The bot shouldn't listen to itself

        # Automated user self-roles
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        selfroles_msg_ids = self._conv_to_id_list(selfrole_list.find('message').find('id').text)
        selfroles_roles_ch = int(selfrole_list.find('channel').find('id').text)
        guild = self.bot.get_guild(payload.guild_id)

        if payload.message_id in selfroles_msg_ids and payload.channel_id == selfroles_roles_ch:  # and selfrole_list.get('Status') == 'Enabled':
            author_role_names = {str(role) for role in guild.get_member(payload.user_id).roles}
            for group in associations.findall('group'):
                req_role = group.find('req_role').text
                if req_role and not req_role in author_role_names:
                    continue
                for assoc in group.findall('assoc'):
                    if str(payload.emoji) == assoc.find('emoji').text:
                        await guild.get_member(payload.user_id).add_roles(
                            discord.utils.get(guild.roles, id=int(assoc.find('role').find('id').text)))
                        break
                        

    async def on_raw_reaction_remove(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # automated user self-roles
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        selfroles_msg_ids = self._conv_to_id_list(selfrole_list.find('message').find('id').text)
        selfroles_roles_ch = int(selfrole_list.find('channel').find('id').text)
        guild = self.bot.get_guild(payload.guild_id)

        if payload.message_id in selfroles_msg_ids and payload.channel_id == selfroles_roles_ch:  # and selfrole_list.get('Status') == 'Enabled':
            for assoc in associations.iter():
                if assoc.tag != 'assoc':
                    continue
                if str(payload.emoji) == assoc.find('emoji').text:
                    await guild.get_member(payload.user_id).remove_roles(
                        discord.utils.get(guild.roles, id=int(assoc.find('role').find('id').text)))
                    break
                    

    def _find_role_assoc(self, role: discord.Role) -> ('tree', 'assoc', 'group'):
        tree = ET.parse('server_data/{}/config.xml'.format(role.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        for group in associations.findall('group'):
            for assoc in group.findall('assoc'):
                if assoc.find('role').find('id').text == str(role.id):
                    return tree, assoc, group
        return tree, None, None


    async def _get_single_group_msg(self, group: "XML Element") -> discord.Embed:
        title = "Group **{}**\n".format(group.find('name').text)
        req_role = group.find('req_role').text
        desc = ""
        if req_role:
            desc = "(requires {})".format(req_role)
        added_element = False
        assoc_list = group.findall('assoc')
        msg_left = ""
        msg_right = ""
        divider = len(assoc_list)/2
        for index in range(len(assoc_list)):
            assoc = assoc_list[index]
            added_element = True
            msg = "\t" + assoc.find('emoji').text + ' **:** ' + str(assoc.find('role').find('name').text) + ' ​ ​\n'
            if index < divider:
                msg_left += msg
            else:
                msg_right += msg
        embed = discord.Embed(title=title, description=desc)
        if not added_element:
            msg_left = "Empty!"
        embed.add_field(name="----------------------", value=msg_left, inline=True)
        if msg_right:
            embed.add_field(name="----------------------", value=msg_right, inline=True)
        return embed


    async def _edit_selfrole_msg(self, guild: discord.Guild, group: "XML Element", change_emoji: bool, emoji: AllEmoji = None, to_add: bool = None):
        """
        Adds or removes a role from the corresponding message if it exists.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(guild.id))
        selfrole_list = tree.find('selfroles')
        channel_id = int(selfrole_list.find('channel').find('id').text)
        if channel_id != -42:
            group_msg_id = int(group.find('message').find('id').text)
            msg_obj = await self.bot.get_channel(channel_id).get_message(group_msg_id)
            embed = await self._get_single_group_msg(group)
            await msg_obj.edit(embed=embed)
            if change_emoji:
                if to_add:
                    await msg_obj.add_reaction(emoji)
                else:
                    await msg_obj.remove_reaction(emoji, self.bot.user)


    async def on_guild_role_delete(self, before: discord.Role):
        tree, assoc, group = self._find_role_assoc(before)
        if assoc:
            emoji = await AllEmoji().convert(None, assoc.find('emoji').text)
            group.remove(assoc)
            tree.write('server_data/{}/config.xml'.format(str(before.guild.id)))
            await self._edit_selfrole_msg(before.guild, group, True, emoji, False)


    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        tree, assoc, group = self._find_role_assoc(before)
        if assoc:
            assoc.find('role').find('name').text = after.name
            tree.write('server_data/{}/config.xml'.format(str(before.guild.id)))
            await self._edit_selfrole_msg(before.guild, group, False)


    def _conv_to_id_list(self, msg_id_text: str) -> [int]:
        """

        :param msg_id_text: the msg_id element's text in a server_data document
        :return: The list of ids of messages
        """
        return list(map(int, msg_id_text.strip().split()))
'''
    async def on_message(self, message):
        await self.bot.process_commands(message)
        tree = ET.parse('server_data/{}/config.xml'.format(message.guild.id))


def setup(bot):
    bot.add_cog(AutomationsCog(bot))
