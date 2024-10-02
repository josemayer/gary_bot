import discord
from utils.helpers import format_duration
from datetime import timedelta
import numpy as np

class PageButtons(discord.ui.View):
    def __init__(self, message, embed, timeout=30):
        super().__init__(timeout=timeout)
        self.message = message
        self.embed = embed
        self.totalPages = self.embed.totalPages
        self.initialPage = self.embed.current    

        prev_button = discord.ui.Button(custom_id="prev", label="<", style=discord.ButtonStyle.primary, disabled=self.initialPage <= 1)
        prev_button.callback = self.prev_action

        status_button = discord.ui.Button(custom_id="status", label=f"Página {self.initialPage}/{self.totalPages}", style=discord.ButtonStyle.primary, disabled=True)

        next_button = discord.ui.Button(custom_id="next", label=">", style=discord.ButtonStyle.primary, disabled=self.initialPage >= self.totalPages)
        next_button.callback = self.next_action

        self.add_item(prev_button)
        self.add_item(status_button)
        self.add_item(next_button)

    async def prev_action(self, interaction:discord.Interaction):
        curr_page, embed_page = self.embed.prevPage()
        self.children[0].disabled = curr_page <= 1
        self.children[1].label = f"Página {curr_page}/{self.totalPages}"
        self.children[2].disabled = curr_page >= self.totalPages
        await interaction.response.edit_message(embed=embed_page, view=self)

    async def next_action(self, interaction:discord.Interaction):
        curr_page, embed_page = self.embed.nextPage()
        self.children[0].disabled = curr_page <= 1
        self.children[1].label = f"Página {curr_page}/{self.totalPages}"
        self.children[2].disabled = curr_page >= self.totalPages
        await interaction.response.edit_message(embed=embed_page, view=self)

    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        await self.message.edit(view=self)

class HelpEmbed:
    def __init__(self, help_info, client):
        self.help_info = help_info
        self.totalPages = len(self.help_info)
        self.current = 1
        self.embed = discord.Embed(
            title=":microscope: Gary Bot",
            description="Olá, agente! Meu nome é Gary, o pinguim inventor! Fui recrutado para executar pequenas missões cotidianas que lhe podem ser úteis. Se restarem dúvidas, não hesite em me contatar pelo celular da EPF. Estarei na minha oficina!",
            color=0x003366
        )
        self.embed.set_thumbnail(url='https://i.imgur.com/fWskrI4.png')
        self.embed.set_footer(text=f"{client.user}: Quantos pares de meia eu tenho?", icon_url=client.user.avatar.url)
        self.updateEmbed()

    def updateEmbed(self):
        if self.embed.fields:
            self.embed.clear_fields()

        for i, (key, value) in enumerate(self.help_info.items(), start=1):
            if i == self.current:
                lines = []
                for j, cmd in enumerate(value['content']):
                    line = f"`{j + 1}.` {cmd['header']}"
                    if cmd['desc']:
                        line += f"\n> {cmd['desc']}"
                    lines.append(line)
                valueField = "\n".join(lines)
                self.embed.add_field(name=self.help_info[key]['title'], value=valueField, inline=False)
                break
    
    def nextPage(self):
        if self.current < self.totalPages:
            self.current += 1
            self.updateEmbed()
        return self.current, self.embed

    def prevPage(self):
        if self.current > 1:
            self.current -= 1
            self.updateEmbed()
        return self.current, self.embed

class QueueEmbed:
    def __init__(self, numByPages, queue):
        self.queue = queue
        self.queue_size = len(queue)
        self.current = 1
        self.numByPages = numByPages
        self.firstElement = 1
        self.totalPages = max(int(np.ceil(self.queue_size / numByPages)), 1)

        self.queue_info = ""
        
        i = 1
        current_track = "`" + str(i) + ".` [" + self.queue[0]['obj'].title + "](" + self.queue[0]['obj'].watch_url + ") `(" + format_duration(self.queue[0]['obj'].length) + ")`"
        
        self.embed = discord.Embed(title=f":loud_sound: Tocando agora", description=current_track, color=0x7b0ec9)
        self.embed.set_footer(text=f"{self.queue_size} músicas na fila • Duração total: {self.calculateTotalDuration()}")
        i += 1
        self.updateEmbed(i)

    def updateEmbed(self, index):
        if len(self.embed.fields) > 0:
            self.embed.remove_field(0)

        self.queue_info = ""

        for music in self.queue[self.firstElement:self.firstElement + self.numByPages]:
            self.queue_info += "`" + str(index) + ".` [" + music['obj'].title + "](" + music['obj'].watch_url + ") `(" + format_duration(music['obj'].length) + ")`\n"
            index += 1

        if self.queue_info != "":
            self.embed.insert_field_at(0, name=f":headphones: Lista de reprodução", value=self.queue_info, inline=False)

    def updateFirstElement(self):
        return (self.numByPages * (self.current - 1)) + 1

    def nextPage(self):
        if self.current + 1 > self.totalPages:
            return (-1, self.embed)
        else:
            self.current += 1
            self.firstElement = self.updateFirstElement()
            self.updateEmbed(self.firstElement + 1)
            return (self.current, self.embed)

    def prevPage(self):
        if self.current - 1 < 1:
            return (-1, self.embed)
        else:
            self.current -= 1
            self.firstElement = self.updateFirstElement()
            self.updateEmbed(self.firstElement + 1)
            return (self.current, self.embed)

    def calculateTotalDuration(self):
        music_time = timedelta(0)
        for music in self.queue:
            music_time += timedelta(seconds=music['obj'].length)
        return str(music_time)

