# IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
import discord
# Import the os module, load_dotenv function from dotenv module.
import os
from dotenv import load_dotenv
# from discord.ext.commands import bot
from discord.ext import commands

import base64
from bitstring import BitArray

# list of countries on each side; None corresponds to cancelled neutral nations, which have codepoints assigned to them
# on that faction but are not playable on that faction (e.g. vanilla: redfor sweden, blufor finland)
# list is in order of display in TShowRoomDeckSerializer - binary value of index corresponds to that stored in deckcode

# vanilla
# countries_nato = ["USA", "UK", "France", "West Germany", "Canada", "Denmark", "Sweden", "Norway", "ANZAC", "Japan",
#                   "South Korea", "Netherlands", "Israel", None, None, "South Africa"]
# countries_pact = ["East Germany", "USSR", "Poland", "Czechoslovakia", "China", "North Korea", "Finland", "Yugoslavia",
#                   None]

# 1991
countries_nato = [":flag_us:", ":flag_gb:", ":flag_fr:", ":flag_de:", ":flag_dk:", ":flag_se:", ":flag_no:",
                  ":flag_au::flag_nz::flag_sg::flag_my:", ":flag_jp:", ":flag_kr:", ":flag_be::flag_nl::flag_lu:",
                  ":flag_il:", ":flag_fi:", "<:flag_yu:1091837130424197120>"]
countries_pact = ["<:flag_od:1091901486264504392>", "<:flag_su:1091901283981611018>", ":flag_pl:", ":flag_cz:",
                  ":flag_cn:", ":flag_kp:", ":flag_fi:", "<:flag_yu:1091837130424197120>", None,
                  ":flag_hu::flag_ro::flag_bg:"]

# BWC-mod
# countries_nato = [":flag_us:", ":flag_gb:", ":flag_fr:", ":flag_de:", None, ":flag_sa::flag_ae::flag_kw:",
#                   ":flag_no::flag_se::flag_dk:", ":flag_au::flag_nz::flag_sg:", ":flag_jp:", ":flag_kr:",
#                   ":flag_ca::flag_nl:", ":flag_il:", ":flag_it::flag_es::flag_pt:"]
# countries_pact = [":flag_ir:", ":flag_in", ":flag_rs:", ":flag_pk:", ":flag_ru:", ":flag_pl::flag_cz::flag_sk:",
#                   ":flag_dz:", ":flag_cn:", ":flag_kp:"]

# corresponding IDs for units on both sides which do not follow regular order

# 1991
# in order: RIMa, BTR-50PK, BVP-2 Vz. 86, Newa-SC, OT-810D
nato_specials = [433, 1301, 1302, 1303, 1304]
pact_specials = [987, 92, 658, 669, 674]
# names are of the original instance and do not necessarily match in-game names


# Loads the .env file that resides on the same level as the script.
load_dotenv()
# Grab the API token from the .env file.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# sets intents for the bot
intents = discord.Intents.all()

# creates the client
bot = commands.Bot(command_prefix='!', intents=intents)


# bot goes online
@bot.event
async def on_ready():
    print("-------------------------------------------------------------------------\nbatbot is online")


@bot.command(name="bat")
async def bat_emoji(ctx):
    await ctx.send(":bat:")


@bot.command(name="convert")
async def convert_deckcode(ctx, arg=None):
    if not arg or arg == "\n":
        return
    t = str(arg).split(" ")[0]
    if not t.startswith("@") or t == "@":
        print("invalid argument - no deck code")
        return
    iCode = BitArray(bytes=base64.b64decode(t.strip("@").encode("ascii"))).bin  # strip leading @ and convert to bits
    # begin parsing the data
    redfor = int(iCode[0:2], 2)  # if nation is redfor or not
    nation = int(iCode[2:7], 2)  # nation val stored as integer
    # coalition = iCode[7:12]  # coalition cant change sides, is always same val for nat deck
    # finish validation here and initialize output string
    if nation >= max(len(countries_nato), len(countries_pact)):
        # if the nation code matches the non-national deck value
        await ctx.reply("Can only convert national decks from valid nations")
        return
    elif redfor and countries_pact[nation] in countries_nato:
        # initialize deckstring as blufor, the country's blufor code, and non-coalition
        iCodeReadable = ["00", bin(nation).removeprefix("0b").zfill(5)]  # testing output
        oCodeHeader = "00" + bin(countries_nato.index(countries_pact[nation])).removeprefix("0b").zfill(5)
        oCodeReadable = ["00", bin(countries_nato.index(countries_pact[nation])).removeprefix("0b").zfill(5)]
        nation = countries_pact[nation]
        ifac = ":red_square:"
        ofac = ":blue_square:"
    elif not redfor and countries_nato[nation] in countries_pact:
        # initialize deckstring as redfor, the country's redfor code, and non-coalition
        iCodeReadable = ["01", bin(nation).removeprefix("0b").zfill(5)]
        oCodeHeader = "01" + bin(countries_pact.index(countries_nato[nation])).removeprefix("0b").zfill(5)
        oCodeReadable = ["00", bin(countries_pact.index(countries_nato[nation])).removeprefix("0b").zfill(5)]
        nation = countries_nato[nation]
        ifac = ":blue_square:"
        ofac = ":red_square:"
    else:
        if redfor:
            await ctx.reply("Cannot convert " + countries_pact[nation] + " to BLUFOR!")
            return
        else:
            await ctx.reply("Cannot convert " + countries_nato[nation] + " to REDFOR!")
            return
    oCodeHeader += iCode[7:17]  # spec, era remain unchanged
    # number of double transport cards
    num2Tcards = int(iCode[17:21], 2)  # can convert to int straight away since this num doesn't change
    num2Tcards_o = num2Tcards
    end2Tcards = 26 + (36 * num2Tcards)
    code2Tcards = iCode[26:end2Tcards]
    # number of single transport cards
    num1Tcards = int(iCode[21:26], 2)
    num1Tcards_o = num1Tcards
    end1Tcards = end2Tcards + (25 * num1Tcards)
    code1Tcards = iCode[end2Tcards:end1Tcards]
    # rest of the cards
    codeOtherCards = iCode[end1Tcards:]
    numOtherCards = int(len(codeOtherCards) / 14)
    numOtherCards_o = numOtherCards
    # not appending the card number counts to the output for now: must re-evaluate after its checked
    oCode = ""  # initialize separate var for the card section itself - will be merged at the end
    iCodeReadable.extend([iCode[7:12], iCode[12:15], iCode[15:17], iCode[17:21], iCode[21:26], "|"])
    oCodeReadable.extend([iCode[7:12], iCode[12:15], iCode[15:17], iCode[17:21], iCode[21:26], "|"])

    for i in range(num2Tcards):  # iterate over the double transport cards
        skip = False  # used to skip the card if it is invalid
        # isolate the block of bits to evaluate for each card in this category (36)
        card = code2Tcards[36 * i:36 * (i + 1)]
        # save the veterancy for rebuilding the new deckstring
        translated_card = card[0:3]
        # isolate the ID for the unit and the two transports
        # convert the ID to an integer
        card = [int(card[3:14], 2), int(card[14:25], 2), int(card[25:36], 2)]
        iCodeReadable.extend([card[0:3], card[3:14], card[14:25], card[25:36]])
        oCodeReadable.append(card[0:3])
        for unit in card:  # evaluate each unit
            if redfor:
                if unit in pact_specials:  # if special case, lookup corresponding value
                    translated_card += bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11))
                elif 795 < unit < 978:  # otherwise, if in normal range, calc by add/subtract
                    translated_card += bin(unit + 322).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(unit + 322).removeprefix("0b").zfill(11))
                elif 771 < unit < 776:  # finnish T-55s are separate for some reason
                    translated_card += bin(unit + 341).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(unit + 341).removeprefix("0b").zfill(11))
                else:  # if unit is not found: either an unhandled special case, or a blufor boat
                    skip = True
                    num2Tcards_o -= 1
                    break
            else:
                if unit in nato_specials:
                    translated_card += bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11))
                elif 1113 < unit < 1118:
                    translated_card += bin(unit - 341).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(unit - 341).removeprefix("0b").zfill(11))
                elif 1117 < unit < 1300:
                    translated_card += bin(unit - 322).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(unit - 322).removeprefix("0b").zfill(11))
                else:
                    skip = True
                    num2Tcards_o -= 1
                    break
        if not skip:
            oCode += translated_card

    iCodeReadable.append("|")
    oCodeReadable.append("|")

    for i in range(num1Tcards):  # Iterate over the single transport cards
        # isolate the block of bits to evaluate for each card in this category (25)
        # this code is more or less identical to the above for-loop
        skip = False
        card = code1Tcards[25 * i:25 * (i + 1)]
        translated_card = card[0:3]
        card = [int(card[3:14], 2), int(card[14:25], 2)]
        iCodeReadable.extend([card[0:3], card[3:14], card[14:25]])
        oCodeReadable.append(card[0:3])
        for unit in card:
            if redfor:
                if unit in pact_specials:
                    translated_card += bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11))
                elif 795 < unit < 978:
                    translated_card += bin(unit + 322).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(unit + 322).removeprefix("0b").zfill(11))
                elif 771 < unit < 776:
                    translated_card += bin(unit + 341).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(unit + 341).removeprefix("0b").zfill(11))
                else:
                    skip = True
                    num1Tcards_o -= 1
                    break
            else:
                if unit in nato_specials:
                    translated_card += bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11))
                elif 1113 < unit < 1118:
                    translated_card += bin(unit - 341).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(unit - 341).removeprefix("0b").zfill(11))
                elif 1117 < unit < 1300:
                    translated_card += bin(unit - 322).removeprefix("0b").zfill(11)
                    oCodeReadable.append(bin(unit - 322).removeprefix("0b").zfill(11))
                else:
                    skip = True
                    num1Tcards_o -= 1
                    break
        if not skip:
            oCode += translated_card

    iCodeReadable.append("|")
    oCodeReadable.append("|")

    # iterate over the rest of the cards
    for i in range(numOtherCards):
        skip = False
        # isolate the block of bits to evaluate for each card in this category (14)
        # this code is more or less identical to the above for-loop, except only one unit, so no inner loop
        card = codeOtherCards[14 * i:14 * (i + 1)]
        translated_card = card[0:3]
        unit = int(card[3:14], 2)
        iCodeReadable.extend([card[0:3], card[3:14]])
        oCodeReadable.append(card[0:3])
        if redfor:
            if unit in pact_specials:  # if special case, lookup corresponding value
                translated_card += bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11)
                oCodeReadable.append(bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11))
            elif 795 < unit < 978:  # otherwise, if in normal range, calc by add/subtract
                translated_card += bin(unit + 322).removeprefix("0b").zfill(11)
                oCodeReadable.append(bin(unit + 322).removeprefix("0b").zfill(11))
            elif 771 < unit < 776:  # finnish T-55s are separate for some reason
                translated_card += bin(unit + 341).removeprefix("0b").zfill(11)
                oCodeReadable.append(bin(unit + 341).removeprefix("0b").zfill(11))
            else:
                numOtherCards_o -= 1
                skip = True
        else:
            if unit in nato_specials:
                translated_card += bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11)
                oCodeReadable.append(bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11))
            elif 1113 < unit < 1118:
                translated_card += bin(unit - 341).removeprefix("0b").zfill(11)
                oCodeReadable.append(bin(unit - 341).removeprefix("0b").zfill(11))
            elif 1117 < unit < 1300:
                translated_card += bin(unit - 322).removeprefix("0b").zfill(11)
                oCodeReadable.append(bin(unit - 322).removeprefix("0b").zfill(11))
            else:
                numOtherCards_o -= 1
                skip = True
        if not skip:
            oCode += translated_card
    # now that new number of cards in 2T and 1T is known, append
    oCodeHeader += bin(num2Tcards_o).removeprefix("0b").zfill(4) + bin(num1Tcards_o).removeprefix("0b").zfill(5)
    oCode = oCodeHeader + oCode
    # log if any cards were removed in the process
    diff = num2Tcards + num1Tcards + numOtherCards - num2Tcards_o - num1Tcards_o - numOtherCards_o
    if diff:
        diff = f"\n{diff} invalid card{' was' if diff == 1 else 's were'} removed"
    else:
        diff = ""
    # lastly, need to re-encode the deck binary into base 64
    o_deckstring = base64.b64encode(BitArray(bin=oCode).tobytes())  # re-encode into base64
    o_deckstring = "@" + str(o_deckstring).strip("b\'")  # clean up formatting
    await ctx.reply(f"Converted  {ifac} {nation}  to  {ofac}{diff}")
    await ctx.send(o_deckstring)
    return

# bot sees message
# @bot.event
# async def on_message(message):
#     if str(message.content).startswith("!"):
#         await bot.process_commands(message)
#         # await message.reply("its over")
#     elif not message.author == bot.user:
#         await message.channel.send("its over")

bot.run(DISCORD_TOKEN)
