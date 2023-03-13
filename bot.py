import os
import time
import openai
import random
import base64
import discord
from io import BytesIO
import banana_dev as banana
from discord import Intents
from discord.ext import commands
from discord.ext.audiorec import NativeVoiceClient

# Banana Keys
api_key = os.environ["BANANA_API_KEY"]
model_key = os.environ["BANANA_MODEL_KEY"]
# Set OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Global vars
intents = Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)
vc = None

# Start the Discord client
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.command()
async def join(ctx: commands.Context):
    global vc
    channel: discord.VoiceChannel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)
    vc = await channel.connect(cls=NativeVoiceClient)
    await ctx.invoke(client.get_command('rec'))

@client.command()
async def leave(ctx: commands.Context):
    if ctx.voice_client:
        # ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        print(f"Disconnected from channel")
    else:
        await ctx.send("You are not in a voice channel.")

@client.command()
async def rec(ctx):
    ctx.voice_client.record(lambda e: print(f"Exception: {e}"))
    embedVar = discord.Embed(title="Started the Recording!",
                             description="use !stop to stop!", color=0x546e7a)
    await ctx.send(embed=embedVar)

@client.command()
async def stop(ctx: commands.Context):
    global vc
    # Recording stop
    if not ctx.voice_client.is_recording():
        return
    await ctx.send(f'Recording stopped')
    print("Recording stopped")
    wav_bytes = await ctx.voice_client.stop_record()
    name = str(random.randint(000000, 999999))
    # Write to wav file
    with open(f'{name}.wav', 'wb') as f:
        f.write(wav_bytes)
    #Read wav file
    with open(f'{name}.wav','rb') as file:
        mp3bytes = BytesIO(file.read())
    mp3 = base64.b64encode(mp3bytes.getvalue()).decode("ISO-8859-1")
    model_payload = {"mp3BytesString":mp3}
    t1 = time.time()
    #Send to Banana for speech2text
    print("Starting Banana")
    speech_to_text = banana.run(api_key,model_key,model_payload)
    t2 = time.time()
    print("Banana whisper finished in ",t2-t1,"seconds")
    whisper_text = speech_to_text["modelOutputs"][0]["text"]
    print(whisper_text)
    await ctx.send(whisper_text)
    # Output whisper text to log and discord
    print("Starting OpenAi Translate")
    t3 = time.time()
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Translate the following English text to Japanese: \"{whisper_text}\"",
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.7,
    )
    t4 = time.time()
    print("OpenAi in ",t4-t3,"seconds")
    # Print the translated Japanese text
    translated_text = response.choices[0].text.strip()
    print(translated_text)
    await ctx.send(translated_text)
    await ctx.voice_client.disconnect()

TOKEN = os.environ["DISCORD_TOKEN"]
client.run(TOKEN)

