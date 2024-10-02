from discord.ext import commands
from utils.helpers import get_weather_time_data
from datetime import datetime, timedelta, timezone

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='report')
    async def report_command(self, ctx, *, city: str):
        if city is None:
            await ctx.send(':exclamation: Informe uma cidade, CEP, bairro ou coordenadas')
            return

        city_data = await get_weather_time_data(city)

        if city_data is None:
            await ctx.send(':question: Localidade não encontrada')
            return

        tz_offset = timezone(timedelta(hours=city_data['tzoffset']))
        current_time = datetime.now(tz_offset).strftime("%d/%m/%Y, %H:%M")

        await ctx.send(f":bar_chart: **Relatório de {city_data['resolvedAddress']}**:\n\n:alarm_clock: {current_time}\n:thermometer: {city_data['currentConditions']['temp']} °C, {city_data['currentConditions']['humidity']}% de umidade, {city_data['currentConditions']['conditions']}")

def setup(bot):
    bot.add_cog(General(bot))
