from datetime import timedelta, datetime
from commands.formatting.T10Commands import t10formatting, t10membersformatting
from commands.formatting.EventCommands import GetCurrentEventID, GetCutoffFormatting, GetEventName
from commands.formatting.GameCommands import GetEventTimeLeftSeconds
from commands.formatting.DatabaseFormatting import getChannelsToPost, removeChannelFromDatabase, updatesDB, getNewsChannelsToPost, getCutoffChannels, rmChannelFromCutoffDatabase, removeChannelFromDatabaseSongs
from commands.apiFunctions import GetBestdoriCutoffAPI
from discord.ext import commands
from tabulate import tabulate
from pytz import timezone
from jsondiff import diff
import asyncio, json, requests, discord

class Loops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        with open("config.json") as file:
            config_json = json.load(file)
            loops_enabled = config_json['loops_enabled']
        self.initialT100Cutoffs = requests.get('https://bestdori.com/api/tracker/data?server=1&event=77&tier=0').json()
        self.initialT1000Cutoffs = requests.get('https://bestdori.com/api/tracker/data?server=1&event=77&tier=1').json()
        self.firstAPI = requests.get('https://bestdori.com/api/news/all.5.json').json()

        if loops_enabled == 'true':
            self.bot.loop.create_task(self.postEventT102min())
            self.bot.loop.create_task(self.postEventT101hr())
            self.bot.loop.create_task(self.postEventNotif('en'))
            self.bot.loop.create_task(self.postEventNotif('jp'))
            self.bot.loop.create_task(self.postSongUpdates1min())
            self.bot.loop.create_task(self.postT1000CutoffUpdates())
            self.bot.loop.create_task(self.postT100CutoffUpdates())
            self.bot.loop.create_task(self.postBestdoriNews())

        else:
            print('Not loading loops')
        print('Successfully loaded Loops cog')

    async def postEventT102min(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            
            try:
                EnEventID = await GetCurrentEventID('en')
            except Exception as e:
                print('Failed posting 2 minute data. Exception: ' + str(e))            
            if EnEventID:
                timeLeftEn = await GetEventTimeLeftSeconds('en', EnEventID)
                if(timeLeftEn > 0):
                    EnMessage = await t10formatting('en', EnEventID, True)
                    #await t10logging('en', EnEventID, False)
                    #await t10logging('en', EnEventID, True)
                    ids = getChannelsToPost(2, 'en')
                    for i in ids:
                        channel = self.bot.get_channel(i)
                        if channel != None:
                            try:
                                await channel.send(EnMessage)
                            except commands.BotMissingPermissions: 
                                LoopRemovalUpdates = self.bot.get_channel(523339468229312555)
                                await LoopRemovalUpdates.send('Removing 2 minute updates from channel: ' + str(channel.name) + " in server: " + str(channel.guild.name))
                                removeChannelFromDatabase(channel, 2, 'en')
                                
            JPEventID = await GetCurrentEventID('jp')
            if JPEventID:
                timeLeftJp = await GetEventTimeLeftSeconds('jp', JPEventID)
                if(timeLeftJp > 0):
                    JPMessage = await t10formatting('jp', JPEventID, True)
                    ids = getChannelsToPost(2, 'jp')
                    for i in ids:
                        channel = self.bot.get_channel(i)
                        if channel != None:
                            try:
                                await channel.send(JPMessage)
                            except commands.BotMissingPermissions: 
                                LoopRemovalUpdates = self.bot.get_channel(523339468229312555)
                                await LoopRemovalUpdates.send('Removing 2 minute updates from channel: ' + str(channel.name) + " in server: " + str(channel.guild.name))
                                removeChannelFromDatabase(channel, 2, 'jp')
            timeStart = datetime.now()
            if (timeStart.minute % 2) != 0: 
                timeFinish = (timeStart + timedelta(minutes=1)).replace(second=0, microsecond=0).timestamp()
            else:
                timeFinish = (timeStart + timedelta(minutes=2)).replace(second=0, microsecond=0).timestamp()
            timeStart = timeStart.timestamp()
            await asyncio.sleep(timeFinish - timeStart)

    async def postEventT101hr(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            timeStart = datetime.now()
            timeFinish = (timeStart + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0).timestamp()            
            timeStart = timeStart.timestamp()
            await asyncio.sleep(timeFinish - timeStart)

            try:
                EnEventID = await GetCurrentEventID('en')
            except Exception as e:
                print('Failed posting 2 minute data. Exception: ' + str(e))            


            if EnEventID:
                timeLeftEn = await GetEventTimeLeftSeconds('en', EnEventID)
                if(timeLeftEn > 0):
                    EnMessage = await t10formatting('en', EnEventID, True)
                    #await t10logging('en', EnEventID, False)
                    #await t10logging('en', EnEventID, True)
                    ids = getChannelsToPost(3600, 'en')
                    for i in ids:
                        channel = self.bot.get_channel(i)
                        if channel != None:
                            try:
                                await channel.send(EnMessage)
                            except commands.BotMissingPermissions: 
                                LoopRemovalUpdates = self.bot.get_channel(523339468229312555)
                                await LoopRemovalUpdates.send('Removing 1 hour updates from channel: ' + str(channel.name) + " in server: " + str(channel.guild.name))
                                removeChannelFromDatabase(channel, 3600, 'en')
            
            JPEventID = await GetCurrentEventID('jp')
            if JPEventID:
                timeLeftJp = await GetEventTimeLeftSeconds('jp', JPEventID)
                if(timeLeftJp > 0):
                    JPMessage = await t10formatting('jp', JPEventID, True)
                    ids = getChannelsToPost(3600, 'jp')
                    for i in ids:
                        channel = self.bot.get_channel(i)
                        if channel != None:
                            try:
                                await channel.send(JPMessage)
                            except commands.BotMissingPermissions: 
                                LoopRemovalUpdates = self.bot.get_channel(523339468229312555)
                                await LoopRemovalUpdates.send('Removing 1 hour updates from channel: ' + str(channel.name) + " in server: " + str(channel.guild.name))
                                removeChannelFromDatabase(channel, 3600, 'jp')                  

    async def postSongUpdates1min(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                timeStart = datetime.now()
                timeFinish = (timeStart + timedelta(minutes=1)).replace(second=0, microsecond=0).timestamp()
                timeStart = timeStart.timestamp()
                await asyncio.sleep(timeFinish - timeStart)
                eventid = await GetCurrentEventID('en')
                if eventid:
                    timeLeft = await GetEventTimeLeftSeconds('en', eventid)
                    if(timeLeft > 0):
                        message = await t10membersformatting('en', eventid, True)
                        #await t10logging('en', eventid, True)
                        ids = getChannelsToPost(1, 'en')
                        for i in ids:
                            channel = self.bot.get_channel(i)
                            if channel != None:
                                try:
                                    for x in message:
                                        await channel.send(x)
                                except commands.BotMissingPermissions: 
                                    LoopRemovalUpdates = self.bot.get_channel(523339468229312555)
                                    await LoopRemovalUpdates.send('Removing 1 minute updates from channel: ' + str(channel.name) + " in server: " + str(channel.guild.name))
                                    removeChannelFromDatabaseSongs(channel)
            except Exception as e:
                print('Failed posting 1 minute song data.\n'+ str(e))

    async def postT100CutoffUpdates(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                EventID = await GetCurrentEventID('en')
                if EventID:
                    timeLeft = await GetEventTimeLeftSeconds('en', EventID)
                    if(timeLeft > 0):
                        ids = getCutoffChannels(100)
                        initialT100Cutoffs = self.initialT100Cutoffs  
                        cutoffAPI = await GetBestdoriCutoffAPI(100)
                        if(sorted(initialT100Cutoffs.items()) != sorted(cutoffAPI.items())):
                            from startup.OpenWebdrivers import enDriver      
                            output = await GetCutoffFormatting(enDriver, 'en', 100)
                            ids = getCutoffChannels(100)
                            for i in ids:
                                channel = self.bot.get_channel(i)
                                if channel != None:
                                    try:
                                        await channel.send('T100 update found!')
                                        await channel.send(embed=output)
                                    except commands.BotMissingPermissions: 
                                        LoopRemovalUpdates = self.bot.get_channel(523339468229312555)
                                        await LoopRemovalUpdates.send('Removing 1 minute updates from channel: ' + str(channel.name) + " in server: " + str(channel.guild.name))
                                        rmChannelFromCutoffDatabase(channel, 100)
                            initialT100Cutoffs = cutoffAPI
                    await asyncio.sleep(60)
            except Exception as e:
                print('Failed posting t100 data.\n'+ str(e))

    async def postT1000CutoffUpdates(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                EventID = await GetCurrentEventID('en')
                if EventID:
                    timeLeft = await GetEventTimeLeftSeconds('en', EventID)
                    if(timeLeft > 0):
                        ids = getCutoffChannels(1000)
                        initialT1000Cutoffs = self.initialT1000Cutoffs  
                        cutoffAPI = await GetBestdoriCutoffAPI(1000)
                        if(sorted(initialT1000Cutoffs.items()) != sorted(cutoffAPI.items())):
                            from startup.OpenWebdrivers import enDriver      
                            output = await GetCutoffFormatting(enDriver, 'en', 1000)
                            ids = getCutoffChannels(1000)
                            for i in ids:
                                channel = self.bot.get_channel(i)
                                if channel != None:
                                    try:
                                        await channel.send('T1000 update found!')
                                        await channel.send(embed=output)
                                    except commands.BotMissingPermissions: 
                                        LoopRemovalUpdates = self.bot.get_channel(523339468229312555)
                                        await LoopRemovalUpdates.send('Removing 1 minute updates from channel: ' + str(channel.name) + " in server: " + str(channel.guild.name))
                                        rmChannelFromCutoffDatabase(channel, 1000)
                            initialT1000Cutoffs = cutoffAPI
                    await asyncio.sleep(60)
            except Exception as e:
                print('Failed posting t1000 data.\n'+ str(e))

    async def postBestdoriNews(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            firstAPI = self.firstAPI
            updatedAPI = requests.get('https://bestdori.com/api/news/all.5.json').json()
            embed=discord.Embed(color=0x09d9fd)
            if(sorted(firstAPI.items()) != sorted(updatedAPI.items())):
                fmt = "%Y-%m-%d %H:%M:%S %Z%z"
                now_time = datetime.now(timezone('US/Eastern'))
                
                jsonDif = diff(firstAPI,updatedAPI)
                for x in jsonDif:
                    if "Patch Note" in jsonDif[x]['tags']:
                        if "EN" in jsonDif[x]['tags']:
                            ids = getNewsChannelsToPost('en')
                        elif "JP" in jsonDif[x]['tags']:
                            ids = getNewsChannelsToPost('jp')
                        elif "CN" in jsonDif[x]['tags']:
                            ids = getNewsChannelsToPost('cn')
                        
                        #post to channels that want all server patch updates as well
                        allids = getNewsChannelsToPost('all')
                        server = jsonDif[x]['tags'][2]
                        embed.set_thumbnail(url='https://pbs.twimg.com/profile_images/1126155698117562368/mW6W89Gg_200x200.png')
                        embed.add_field(name='New %s Patch Note Available!' % server.upper(), value='https://bestdori.com/home/news/' + str(x), inline=False)
                        embed.set_footer(text=now_time.strftime(fmt))               
                        for i in ids:
                            channel = self.bot.get_channel(i)
                            if channel != None:
                                await channel.send(embed=embed)
                        for i in allids:
                            channel = self.bot.get_channel(i)
                            if channel != None:
                                await channel.send(embed=embed)

                        embed=discord.Embed(color=0x09d9fd)
                firstAPI = updatedAPI
            await asyncio.sleep(300)

    async def sendEventUpdates(self, message: str, server: str):
        ids = updatesDB(server)
        if(message):
            for i in ids:
                channel = self.bot.get_channel(i)
                if channel != None:
                    await channel.send(message)

    async def postEventNotif(self, server: str):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            from commands.apiFunctions import GetBestdoriEventAPI
            from commands.formatting.EventCommands import GetCurrentEventID
            EventID = await GetCurrentEventID(server)
            eventAPI = await GetBestdoriEventAPI(EventID)
            eventName = await GetEventName(server, EventID)
            currentTime = ((datetime.now().timestamp()) * 1000)
            if server == 'en':
                Key = 1 
            elif server == 'jp':
                Key = 0 
            eventEnd = float(eventAPI['endAt'][Key])
            eventStart = float(eventAPI['startAt'][Key])
            timeTilEventEnd = (int(eventEnd) - currentTime) / 1000
            timeToStart = (eventStart - currentTime) / 1000
            if(timeToStart > 0):
                if (timeToStart > 3600):
                    sleep = int(timeToStart - 3600)
                    await asyncio.sleep(sleep)
                    message = "```The " + server.upper() + " event %s begins in 1 hour!```" %eventName
                    await self.sendEventUpdates(message, 'en')
                    await asyncio.sleep(3600)
                    message = "```The " + server.upper() + " event %s! has begun!```" %eventName
                    await self.sendEventUpdates(message, 'en')
                else:
                    await asyncio.sleep(timeToStart)
                    message = "```The " + server.upper() + " event %s! has begun!```" %eventName
                    await self.sendEventUpdates(message, 'en')
            # check if there's more than 1 day left
            elif(timeTilEventEnd > 86400):
                timeTo1DayLeft = (eventEnd - 86400000)
                sleep = int((timeTo1DayLeft - currentTime) / 1000)
                await asyncio.sleep(sleep)
                message = "```There is 1 day left in the " + server.upper() + " event %s!```" %eventName
                await self.sendEventUpdates(message, 'en')
                await asyncio.sleep(82800000 / 1000)
                message = "```There is 1 hour left in the " + server.upper() + " event %s!```" %eventName
                await self.sendEventUpdates(message, 'en')
                await asyncio.sleep(3600)
                message = "```The " + server.upper() + " event %s has concluded.```" %eventName
                await self.sendEventUpdates(message, 'en')
            await asyncio.sleep(60)

def setup(bot):
    bot.add_cog(Loops(bot))