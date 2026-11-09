import asyncio, json, os, random, shutil, sqlite3, tempfile
from math import isqrt
from pathlib import Path
import discord
from discord.ext import commands

ROOT = Path(os.getenv("BOT_DATA_DIR", "/home/container/data"))
DB_FILE = ROOT / "peak_game.json"
OLD_DB = Path("/home/container/peak_adventure.sqlite3")

CHARACTERS = {
 "sukuna":("Ryomen Sukuna","Jujutsu Kaisen",1,(78,112),"Malevolent Shrine","malevolent_shrine",(155,205),2),
 "gojo":("Satoru Gojo","Jujutsu Kaisen",3,(70,120),"Hollow Purple","hollow_purple",(175,225),2),
 "yuji":("Yuji Itadori","Jujutsu Kaisen",2,(75,115),"Black Flash","black_flash",(145,195),2),
 "naruto":("Naruto Uzumaki","Naruto",4,(88,130),"Rasenshuriken","rasenshuriken",(190,245),2),
 "sasuke":("Sasuke Uchiha","Naruto",6,(92,135),"Kirin","kirin",(205,260),3),
 "luffy":("Monkey D. Luffy","One Piece",7,(95,140),"Bajrang Gun","bajrang_gun",(220,285),3),
 "zoro":("Roronoa Zoro","One Piece",9,(105,150),"King of Hell","king_of_hell",(235,295),3),
 "ichigo":("Ichigo Kurosaki","Bleach",10,(108,155),"Getsuga Tensho","getsuga_tensho",(245,310),3),
 "aizen":("Sosuke Aizen","Bleach",14,(120,170),"Kyoka Suigetsu","kyoka_suigetsu",(275,340),4),
 "goku":("Son Goku","Dragon Ball",15,(130,180),"Spirit Bomb","spirit_bomb",(300,390),4),
 "vegeta":("Vegeta","Dragon Ball",16,(135,185),"Final Flash","final_flash",(310,400),4),
 "tanjiro":("Tanjiro Kamado","Demon Slayer",8,(100,145),"Sun Breathing","sun_breathing",(225,285),3),
 "asta":("Asta","Black Clover",11,(112,160),"Anti-Magic","anti_magic",(250,315),3),
 "deku":("Izuku Midoriya","My Hero Academia",12,(115,165),"One For All","one_for_all",(260,325),3),
 "eren":("Eren Yeager","Attack on Titan",13,(118,168),"Founding Titan","founding_titan",(265,330),4),
 "rimuru":("Rimuru Tempest","That Time I Got Reincarnated as a Slime",18,(145,195),"Predator","predator",(330,420),5),
}
BOSSES = {
 "mahito":("Mahito",1600,(28,46),350,{"cursed_ash":(1,3),"cursed_fingers":(1,2),"transfigured_soul":(1,2),"idle_transfiguration":(1,1),"soul_fragment":(1,3),"black_flash_residue":(1,2)}),
 "doflamingo":("Donquixote Doflamingo",2800,(38,62),650,{"string_core":(1,3),"devil_fruit_shard":(1,2),"birdcage_thread":(1,2),"celestial_blood":(1,1),"ito_essence":(1,2),"flamingo_feather":(1,3)}),
 "madara":("Madara Uchiha",4700,(52,82),1200,{"six_paths_essence":(1,2),"chakra_crystal":(1,3),"susanoo_fragment":(1,2),"rinnegan_shard":(1,1),"god_tree_seed":(1,2),"uchiha_relic":(1,3)}),
 "frieza":("Frieza",7000,(65,98),1900,{"dragon_ball":(1,2),"cosmic_core":(1,2),"frozen_pod":(1,3),"saiyan_armor":(1,2),"tyrant_emblem":(1,1),"zenkai_cell":(1,2)}),
 "gojo":("Satoru Gojo",2200,(32,52),550,{"six_eyes":(1,1),"limitless_core":(1,2),"blue_orb":(1,2),"red_orb":(1,2),"hollow_purple_shard":(1,1),"blindfold_fabric":(1,3)}),
 "sukuna":("Ryomen Sukuna",5600,(58,92),1650,{"cursed_fingers":(1,3),"cursed_ash":(1,2),"sukuna_relic":(1,1),"malevolent_essence":(1,2),"shrine_fragment":(1,2),"king_of_curses_seal":(1,1)}),
 "muzan":("Muzan Kibutsuji",3900,(48,76),1050,{"demon_blood":(1,2),"sunsteel":(1,2),"blue_spider_lily":(1,1),"flesh_core":(1,3),"demon_cell":(1,2),"nightmare_ash":(1,2)}),
 "meruem":("Meruem",6200,(62,94),1800,{"chimera_essence":(1,2),"royal_core":(1,1),"nen_crystal":(1,3),"chimera_scale":(1,2),"royal_guard_token":(1,1),"kingly_aura":(1,2)}),
 "all_for_one":("All For One",5100,(55,86),1450,{"quirk_catalyst":(1,2),"all_for_one_core":(1,1),"stolen_quirk_shard":(1,3),"nomu_tissue":(1,2),"alliance_emblem":(1,1),"impact_relic":(1,2)}),
 "zeref":("Zeref",8200,(72,108),2400,{"ether_core":(1,2),"curse_book":(1,1),"fairy_heart_shard":(1,2),"black_magic_ash":(1,3),"immortality_seal":(1,1),"time_rift_fragment":(1,2)}),
}
ITEMS = {k:k.replace("_"," ").title() for b in BOSSES.values() for k in b[4]}
ITEMS.update({"limitless_core":"Limitless Core","phoenix_feather":"Phoenix Feather","mythic_token":"Mythic Token"})
RACES = {
 "human":("Human",1.0,0.0,"Balanced starting race."),
 "gojo":("Gojo Clan",1.10,.10,"+10% damage and 10% damage reduction."),
 "saiyan":("Saiyan",1.15,0.0,"+15% damage."),
 "fishman":("Fish-Man",1.0,.20,"20% damage reduction."),
 "shinobi":("Shinobi",1.07,.08,"+7% damage and 8% damage reduction."),
 "curse":("Cursed Spirit",1.12,-.05,"+12% damage, takes 5% more damage."),
 "vessel":("Sukuna Vessel",1.12,0.0,"+12% damage; Sukuna's signature skill is free."),
 "sukuna":("King of Curses",1.25,.15,"Secret race: +25% damage and 15% damage reduction."),
}
DEFAULT = {"xp":0,"level":1,"points":0,"character":"sukuna","weapon":None,"weapon_damage_override":None,"unlocked":[],"race":"human","inventory":{},"six_eyes_unlocked":False,"infinity_unlocked":False,"sukuna_race_unlocked":False,"wins":0,"damage":0,"symbolic_rewards":{"xp":0,"points":0,"points_spent":0,"wins":0,"damage":0,"inventory":{},"inventory_spent":{}}}

def apply_level_ups(profile):
 xp=max(0,int(profile.get("xp",0))); level=max(1,int(profile.get("level",1)))
 a=2*level-1
 levels=max(0,(isqrt(a*a+(8*xp)//250)-a)//2)
 cost=lambda n: 125*n*(2*level+n-1)
 while levels and cost(levels)>xp: levels-=1
 while cost(levels+1)<=xp: levels+=1
 profile["xp"]=xp-cost(levels)
 profile["level"]=level+levels
 profile["points"]+=levels
 return levels

def raid_phase(hp,max_hp):
 if max_hp<=0: return 1
 if hp*4<=max_hp: return 4
 if hp*2<=max_hp: return 3
 if hp*4<=max_hp*3: return 2
 return 1

def swarm_value(count):
 return 1 if count == "googolplex" else int(count)

def swarm_label(count):
 return "10^(10^100) (googolplex)" if count == "googolplex" else display_number(count)

def symbolic_quantity(coefficient, spent=0):
 coefficient=int(coefficient); spent=int(spent)
 if coefficient<=0: return "0"
 base="10^(10^100)" if coefficient==1 else f"{display_number(coefficient)} × 10^(10^100)"
 return f"{base} - {spent:,}" if spent else base

def display_number(value):
 value=int(value)
 if value==0: return "0"
 if value.bit_length()<80: return f"{value:,}"
 try:
  digits=str(value)
  return f"{digits[0]}.{digits[1:3] or '00'}e{len(digits)-1}"
 except ValueError:
  bits=value.bit_length()
  exponent=int((bits-1)*0.3010299956639812)
  power=10**max(0,exponent)
  while value<power:
   exponent-=1; power//=10
  while value>=power*10:
   exponent+=1; power*=10
  leading=value*100//power
  return f"{leading/100:.2f}e{exponent}"

def save(data):
 ROOT.mkdir(parents=True,exist_ok=True)
 if DB_FILE.exists():
  try:
   json.loads(DB_FILE.read_text(encoding="utf-8"))
   shutil.copy2(DB_FILE,DB_FILE.with_suffix(".backup.json"))
  except (OSError,json.JSONDecodeError):
   pass
 fd,name=tempfile.mkstemp(dir=ROOT,prefix="peak-",suffix=".tmp")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as f:
   json.dump(data,f,ensure_ascii=False,separators=(",",":")); f.flush(); os.fsync(f.fileno())
  os.replace(name,DB_FILE)
 finally:
  if os.path.exists(name): os.unlink(name)

def load():
 ROOT.mkdir(parents=True,exist_ok=True)
 if DB_FILE.exists():
  try:
   d=json.loads(DB_FILE.read_text(encoding="utf-8"))
   if isinstance(d,dict) and isinstance(d.get("profiles"),dict):
    d.setdefault("raids",{}); d.setdefault("custom_weapons",{}); d.setdefault("version",1); return d
  except (OSError,json.JSONDecodeError):
   try: DB_FILE.replace(DB_FILE.with_suffix(".broken.json"))
   except OSError: pass
 d={"version":1,"profiles":{},"raids":{},"custom_weapons":{}}
 if OLD_DB.exists():
  try:
   con=sqlite3.connect(OLD_DB)
   columns={row[1] for row in con.execute("PRAGMA table_info(profiles)").fetchall()}
   wanted=["user_id","xp","level","skill_points","weapon","unlocked"]
   for col in ["race","six_eyes","infinity_unlocked","six_eyes_unlocked"]:
    if col in columns: wanted.append(col)
   rows=con.execute("SELECT "+",".join(wanted)+" FROM profiles").fetchall(); con.close()
   for row in rows:
    values=dict(zip(wanted,row)); uid=values["user_id"]; char=values["weapon"]
    p=dict(DEFAULT); p.update(xp=values["xp"],level=values["level"],points=values["skill_points"],character=char if char in CHARACTERS else "sukuna",unlocked=list(filter(None,(values["unlocked"] or "").split(","))))
    p["race"]=values.get("race") if values.get("race") in RACES else "human"
    if values.get("six_eyes",0): p["inventory"]["six_eyes"]=values["six_eyes"]
    p["infinity_unlocked"]=bool(values.get("infinity_unlocked",0)); p["six_eyes_unlocked"]=bool(values.get("six_eyes_unlocked",0))
    d["profiles"][str(uid)]=p
  except sqlite3.Error: pass
 save(d); return d

class WeaponBuilderModal(discord.ui.Modal, title="Create a custom weapon"):
 def __init__(self, cog, owner_id):
  super().__init__(timeout=300); self.cog=cog; self.owner_id=owner_id
  self.weapon_name=discord.ui.TextInput(label="Weapon name",placeholder="e.g. World Splitter",max_length=40)
  self.damage=discord.ui.TextInput(label="Basic damage range",placeholder="Example: 100-150",max_length=100)
  self.ability=discord.ui.TextInput(label="Ability name",placeholder="e.g. Reality Sever",max_length=40)
  self.ability_damage=discord.ui.TextInput(label="Ability damage range",placeholder="Example: 200-300",max_length=15)
  self.description=discord.ui.TextInput(label="Description",style=discord.TextStyle.paragraph,required=False,max_length=180)
  for item in (self.weapon_name,self.damage,self.ability,self.ability_damage,self.description): self.add_item(item)
 async def on_submit(self, interaction):
  if interaction.user.id!=self.owner_id:
   await interaction.response.send_message("Only the command owner can submit this builder.",ephemeral=True); return
  try:
   low,high=[int(x.strip()) for x in self.damage.value.split("-",1)]
   skill_low,skill_high=[int(x.strip()) for x in self.ability_damage.value.split("-",1)]
   if not (1<=low<=high and 1<=skill_low<=skill_high): raise ValueError
  except (ValueError,TypeError):
   await interaction.response.send_message("Damage ranges must use MIN-MAX format. Both values must be positive, and the maximum must be at least the minimum.",ephemeral=True); return
  name=self.weapon_name.value.strip(); key=name.lower().replace(" ","_")
  if not key or key in self.cog.data["custom_weapons"] or key in CHARACTERS:
   await interaction.response.send_message("That weapon name is empty or already in use.",ephemeral=True); return
  self.cog.data["custom_weapons"][key]={"name":name,"damage":[low,high],"ability":self.ability.value.strip(),"ability_key":self.ability.value.strip().lower().replace(" ","_"),"ability_damage":[skill_low,skill_high],"description":self.description.value.strip() or "A custom weapon forged by the bot owner."}
  self.cog.flush()
  await interaction.response.send_message(embed=self.cog.embed("WEAPON CREATED",f"**{name}** is now in the weapon archive.\nBasic damage: {low}-{high}\n{self.ability.value}: {skill_low}-{skill_high}\nPlayers can equip it with ,weapon equip {key}."),ephemeral=True)

class WeaponBuilderView(discord.ui.View):
 def __init__(self,cog,owner_id):
  super().__init__(timeout=180); self.cog=cog; self.owner_id=owner_id
 @discord.ui.button(label="Open weapon builder",style=discord.ButtonStyle.primary)
 async def open_builder(self,interaction,button):
  if interaction.user.id!=self.owner_id:
   await interaction.response.send_message("Only the bot owner can use this builder.",ephemeral=True); return
  await interaction.response.send_modal(WeaponBuilderModal(self.cog,self.owner_id))


class Adventure(commands.Cog):
 def __init__(self,bot):
  self.bot=bot; self.data=load(); self.lock=asyncio.Lock()
 def p(self,uid):
  k=str(uid)
  if k not in self.data["profiles"]:
   self.data["profiles"][k]=json.loads(json.dumps(DEFAULT)); save(self.data)
  p=self.data["profiles"][k]
  for key,value in DEFAULT.items(): p.setdefault(key,json.loads(json.dumps(value)))
  if p["character"] not in CHARACTERS: p["character"]="sukuna"
  if p["race"] not in RACES: p["race"]="human"
  p.setdefault("weapon",None)
  p.setdefault("symbolic_rewards",{"xp":0,"points":0,"points_spent":0,"wins":0,"damage":0,"inventory":{},"inventory_spent":{}})
  sr=p["symbolic_rewards"]
  for key,value in {"xp":0,"points":0,"points_spent":0,"wins":0,"damage":0,"inventory":{},"inventory_spent":{}}.items(): sr.setdefault(key,value)
  return p
 def flush(self): save(self.data)
 def embed(self,title,desc="",color=None):
  e=discord.Embed(title=title,description=desc,color=color or discord.Color.from_rgb(48,61,82)); e.set_footer(text="PEAK  /  ANIME CHRONICLES"); return e
 def item(self,p,key,n):
  p["inventory"][key]=max(0,p["inventory"].get(key,0)+n)
  if not p["inventory"][key]: p["inventory"].pop(key,None)
 def has_item(self,p,key,n):
  if p["inventory"].get(key,0)>=n: return True
  sr=p["symbolic_rewards"]; return sr["inventory"].get(key,0)>0
 def consume_item(self,p,key,n):
  normal=p["inventory"].get(key,0); take=min(normal,n)
  if take: self.item(p,key,-take)
  remaining=n-take
  if remaining:
   sr=p["symbolic_rewards"]
   if sr["inventory"].get(key,0)<=0: return False
   sr['inventory_spent'][key]=sr['inventory_spent'].get(key,0)+remaining
  return True

 @commands.command(name="characters",aliases=["roster","weapons"])
 async def characters(self,ctx):
  p=self.p(ctx.author.id); e=self.embed("ANIME CHARACTER ARCHIVE","Equip a character with ,character <key>.")
  for k,c in CHARACTERS.items():
   state="EQUIPPED" if p["character"]==k else ("AVAILABLE" if p["level"]>=c[2] else "LEVEL "+str(c[2]))
   e.add_field(name=f"{c[0]} / {state}",value=f"{c[1]} · {c[3][0]}–{c[3][1]} damage\nSignature: {c[4]}",inline=False)
  await ctx.reply(embed=e,mention_author=False)
 @commands.command(name="character",aliases=["equip"])
 async def character(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_"); p=self.p(ctx.author.id); c=CHARACTERS.get(key)
  if not c or p["level"]<c[2]:
   await ctx.reply(embed=self.embed("Character unavailable","Unknown character or your level is too low."),mention_author=False); return
  p["character"]=key; self.flush()
  await ctx.reply(embed=self.embed("CHARACTER EQUIPPED",f"You equipped {c[0]} from {c[1]}."),mention_author=False)
 @commands.command(name="races")
 async def races(self,ctx):
  p=self.p(ctx.author.id); e=self.embed("RACE REGISTRY",f"Current race: {RACES[p['race']][0]}")
  for k,r in RACES.items():
   if k=="sukuna" and not p["sukuna_race_unlocked"]: continue
   e.add_field(name=r[0],value=f"{r[3]}\nSelect with ,race {k}",inline=False)
  await ctx.reply(embed=e,mention_author=False)
 @commands.command(name="race")
 async def race(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_"); p=self.p(ctx.author.id)
  if key not in RACES or (key=="sukuna" and not p["sukuna_race_unlocked"]):
   await ctx.reply(embed=self.embed("RACE LOCKED","The secret King of Curses race requires 20 Cursed Fingers while using Vessel."),mention_author=False); return
  p["race"]=key; self.flush()
  await ctx.reply(embed=self.embed("RACE CHANGED",f"Your race is now {RACES[key][0]}. {RACES[key][3]}"),mention_author=False)
 @commands.command(name="bosses",aliases=["raids"])
 async def bosses(self,ctx):
  e=self.embed("RAID REGISTER","Each player acts once, then the boss retaliates. Every clear grants at least five guaranteed loot types, plus a chance at a Mythic Token.")
  for k,b in BOSSES.items(): e.add_field(name=f"{b[0]} / {k}",value=f"{b[1]:,} HP · {b[2][0]}–{b[2][1]} damage · {b[3]:,} XP",inline=False)
  await ctx.reply(embed=e,mention_author=False)
 @commands.group(name="boss",invoke_without_command=True)
 async def boss(self,ctx):
  await ctx.reply(embed=self.embed("RAID COMMANDS",",bosses · ,boss challenge <key> · ,boss summon <key> <count> · ,boss status · ,join · ,boss leave · ,boss abandon · ,attack [skill] · ,use phoenix_feather"),mention_author=False)
 @boss.command(name="summon")
 @commands.guild_only()
 @commands.is_owner()
 async def summon(self,ctx,key:str,count:str):
  key=key.lower().strip().replace(" ","_")
  raw_count=count.lower().replace(",","").strip()
  if raw_count == "googolplex": count="googolplex"
  else:
   try: count=int(raw_count)
   except ValueError:
    await ctx.reply(embed=self.embed("INVALID COUNT","Use a whole number or the word googolplex."),mention_author=False); return
  if key not in BOSSES:
   await ctx.reply(embed=self.embed("UNKNOWN TARGET","Use ,bosses to view available bosses."),mention_author=False); return
  if count != "googolplex" and count < 1:
   await ctx.reply(embed=self.embed("INVALID COUNT","Boss count must be at least 1."),mention_author=False); return
  async with self.lock:
   g=str(ctx.guild.id)
   if g in self.data["raids"]:
    await ctx.reply(embed=self.embed("RAID ACTIVE","Finish the current raid first."),mention_author=False); return
   b=BOSSES[key]
   self.data["raids"][g]={"boss":key,"hp":b[1],"max_hp":b[1],"swarm_count":count,"leader":str(ctx.author.id),"players":{str(ctx.author.id):250},"turns":[str(ctx.author.id)],"turn":0,"damage":{},"phase":1}
   self.flush()
  await ctx.reply(embed=self.embed("BOSS SWARM SUMMONED",f"Summoned **{swarm_label(count)} {b[0]}**. This uses one shared-health simulation rather than creating individual boss objects. Each attack hits the entire swarm.\nPer-boss HP: {b[1]:,}\nFirst turn: {ctx.author.mention}. Others can use ,join."),mention_author=False)
 @boss.command(name="challenge")
 @commands.guild_only()
 async def challenge(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_")
  if key not in BOSSES: await ctx.reply(embed=self.embed("UNKNOWN TARGET","Use ,bosses to view the raid register."),mention_author=False); return
  async with self.lock:
   g=str(ctx.guild.id)
   if g in self.data["raids"]: await ctx.reply(embed=self.embed("RAID ACTIVE","Finish the current raid first."),mention_author=False); return
   b=BOSSES[key]; self.data["raids"][g]={"boss":key,"hp":b[1],"max_hp":b[1],"leader":str(ctx.author.id),"players":{str(ctx.author.id):250},"turns":[str(ctx.author.id)],"turn":0,"damage":{}}
   self.flush()
  await ctx.reply(embed=self.embed(f"RAID STARTED / {b[0].upper()}",f"{b[1]:,} HP. First turn: {ctx.author.mention}. Others can use ,join."),mention_author=False)
 @boss.command(name="abandon")
 @commands.guild_only()
 async def abandon_raid(self,ctx):
  g=str(ctx.guild.id); uid=str(ctx.author.id)
  async with self.lock:
   r=self.data["raids"].get(g)
   if not r:
    await ctx.reply(embed=self.embed("NO RAID","There is no active raid to abandon."),mention_author=False); return
   if r.get("leader")!=uid:
    await ctx.reply(embed=self.embed("ACCESS DENIED","Only the player who started the raid can abandon it."),mention_author=False); return
   self.data["raids"].pop(g,None); self.flush()
  await ctx.reply(embed=self.embed("RAID ABANDONED","The active raid has been closed. No rewards were granted."),mention_author=False)

 @commands.command(name="join")
 @commands.guild_only()
 async def join(self,ctx):
  async with self.lock:
   r=self.data["raids"].get(str(ctx.guild.id)); uid=str(ctx.author.id)
   if not r: await ctx.reply(embed=self.embed("NO RAID","Start a raid with ,boss challenge <key>."),mention_author=False); return
   if uid in r["players"]: await ctx.reply(embed=self.embed("ALREADY JOINED","You are already in this raid."),mention_author=False); return
   if len(r["players"])>=6: await ctx.reply(embed=self.embed("PARTY FULL","Raids support up to 6 players."),mention_author=False); return
   r["players"][uid]=250; r["turns"].append(uid)
   added=max(1,int(BOSSES[r["boss"]][1]*0.25)); r["hp"]+=added; r["max_hp"]+=added; self.flush()
  await ctx.reply(embed=self.embed("PLAYER JOINED",f"{ctx.author.mention} entered with 250 HP. Boss health scaled by 25% for the extra party member."),mention_author=False)
 @boss.command(name="status")
 @commands.guild_only()
 async def status(self,ctx):
  r=self.data["raids"].get(str(ctx.guild.id))
  if not r: await ctx.reply(embed=self.embed("NO RAID","There is no active raid."),mention_author=False); return
  b=BOSSES[r["boss"]]; alive=[u for u in r["turns"] if r["players"].get(u,0)>0]; current=alive[r["turn"]%len(alive)] if alive else None
  count=r.get("swarm_count",1)
  title=f"{swarm_label(count)}x {b[0].upper()}" if count != 1 else b[0].upper()
  phase=raid_phase(r['hp'],r['max_hp']); r['phase']=phase
  e=self.embed(title,f"Phase {phase}/4 · {display_number(r['hp'])} / {display_number(r['max_hp'])} HP per boss · {swarm_label(count)} remaining"); e.add_field(name="Current turn",value=f"<@{current}>" if current else "None")
  e.add_field(name="Party",value="\n".join(f"<@{u}> · {hp}/250 HP" for u,hp in r["players"].items())[:1024],inline=False)
  await ctx.reply(embed=e,mention_author=False)
 @boss.command(name="leave")
 @commands.guild_only()
 async def leave_raid(self,ctx):
  g=str(ctx.guild.id); uid=str(ctx.author.id)
  async with self.lock:
   r=self.data["raids"].get(g)
   if not r or uid not in r["players"]:
    await ctx.reply(embed=self.embed("NOT IN RAID","You are not part of the active raid."),mention_author=False); return
   alive=[u for u in r["turns"] if r["players"].get(u,0)>0]
   current=alive[r["turn"]%len(alive)] if alive else None
   turns=r["turns"][:]; idx=turns.index(uid)
   following=next((u for u in turns[idx+1:]+turns[:idx] if u!=uid and r["players"].get(u,0)>0),None)
   r["turns"].remove(uid); r["players"].pop(uid,None); r["damage"].pop(uid,None)
   if r.get("leader")==uid and r["turns"]: r["leader"]=r["turns"][0]
   if not r["players"]:
    self.data["raids"].pop(g,None); self.flush()
    await ctx.reply(embed=self.embed("RAID CLOSED","The last party member left. The raid has been closed."),mention_author=False); return
   alive_now=[u for u in r["turns"] if r["players"].get(u,0)>0]
   if alive_now:
    next_user=following if current==uid and following in alive_now else (current if current in alive_now else alive_now[0])
    r["turn"]=alive_now.index(next_user)
   else:
    r["turn"]=0
   self.flush()
  await ctx.reply(embed=self.embed("LEFT RAID","You left the active party. Your raid contribution has been removed."),mention_author=False)

 @commands.command(name="attack",aliases=["strike","hit"])
 @commands.guild_only()
 @commands.cooldown(1,1,commands.BucketType.user)
 async def attack(self,ctx,ability=None):
  async with self.lock:
   g=str(ctx.guild.id); r=self.data["raids"].get(g); uid=str(ctx.author.id)
   if not r: await ctx.reply(embed=self.embed("NO RAID","Start one with ,boss challenge mahito."),mention_author=False); return
   if uid not in r["players"]: await ctx.reply(embed=self.embed("NOT ENLISTED","Use ,join first."),mention_author=False); return
   alive=[u for u in r["turns"] if r["players"].get(u,0)>0]
   if not alive: self.data["raids"].pop(g,None); self.flush(); await ctx.reply(embed=self.embed("PARTY DEFEATED","Raid ended."),mention_author=False); return
   r["turn"]%=len(alive); current=alive[r["turn"]]
   if current!=uid: await ctx.reply(embed=self.embed("NOT YOUR TURN",f"It is <@{current}>'s turn."),mention_author=False); return
   p=self.p(ctx.author.id); c=CHARACTERS[p["character"]]; custom=self.data.get("custom_weapons",{}).get(p.get("weapon"))
   if custom:
    skill=custom["ability_key"]
    if ability:
     if ability.lower().strip().replace(" ","_")!=skill:
      await ctx.reply(embed=self.embed("UNKNOWN ABILITY",f"This weapon uses {custom['ability']}."),mention_author=False); return
     damage=random.randint(*custom["ability_damage"]); action=custom["ability"]
    else: damage=random.randint(*custom["damage"]); action=custom["name"]+" strike"
    override=p.get("weapon_damage_override")
    if override == "googolplex":
     damage=r["hp"]
    elif override is not None:
     damage=override
   else:
    skill=c[5]
    if ability:
     if ability.lower().strip()!=skill or (skill not in p["unlocked"] and not(p["race"]=="vessel" and p["character"]=="sukuna")):
      await ctx.reply(embed=self.embed("SKILL LOCKED",f"Unlock {skill} with ,unlock {skill}. Vessel gets Sukuna's skill free."),mention_author=False); return
     damage=random.randint(*c[6]); action=c[4]
    else: damage=random.randint(*c[3]); action="Basic strike"
   race=RACES[p["race"]]; race_mult=1.20 if p["race"]=="gojo" and p["six_eyes_unlocked"] else race[1]
   level_mult=1+min(35,max(0,int(p["level"])-1))*0.01
   damage=min(r["hp"],max(1,int(damage*race_mult*level_mult))); r["hp"]-=damage
   previous_phase=r.get("phase",1); phase=raid_phase(r["hp"],r["max_hp"]); r["phase"]=phase
   phase_line=""
   if phase>previous_phase: phase_line=f"\nBoss phase increased to {phase}/4. Incoming attacks are stronger."
   swarm_count=r.get("swarm_count",1); symbolic_swarm=swarm_count=="googolplex"
   swarm_multiplier=1 if symbolic_swarm else swarm_value(swarm_count)
   total_damage=damage*swarm_multiplier
   if symbolic_swarm:
    r["damage"][uid]=r["damage"].get(uid,0)+damage
    p["symbolic_rewards"]["damage"]+=damage
    total_damage_label=f"{display_number(damage)} × 10^(10^100)"
   else:
    r["damage"][uid]=r["damage"].get(uid,0)+total_damage
    p["damage"]+=total_damage
    total_damage_label=display_number(total_damage)
   b=BOSSES[r["boss"]]
   if r["hp"]<=0:
    drops=[]
    for player_id in list(r["players"]):
     q=self.p(int(player_id)); got=[]
     if symbolic_swarm:
      sr=q["symbolic_rewards"]
      xp_reward=b[3]+r["damage"].get(player_id,0)//4
      sr["xp"]+=xp_reward; sr["points"]+=1; sr["wins"]+=1
      got.extend([f"XP x{symbolic_quantity(xp_reward)}",f"Skill Points x{symbolic_quantity(1)}",f"Victories x{symbolic_quantity(1)}"])
      for item,limits in b[4].items():
       amount=random.randint(*limits); sr["inventory"][item]=sr["inventory"].get(item,0)+amount
       got.append(f"{ITEMS.get(item,item)} x{symbolic_quantity(amount)}")
     else:
      q["xp"]+=b[3]*swarm_multiplier+r["damage"].get(player_id,0)//4; q["points"]+=swarm_multiplier; q["wins"]+=swarm_multiplier
      apply_level_ups(q)
      for item,limits in b[4].items():
       amount=random.randint(*limits)*swarm_multiplier
       self.item(q,item,amount); got.append(f"{ITEMS.get(item,item)} x{display_number(amount)}")
     if random.random()<0.08:
      if symbolic_swarm:
       sr=q["symbolic_rewards"]; sr["inventory"]["phoenix_feather"]=sr["inventory"].get("phoenix_feather",0)+1
       got.append(f"Phoenix Feather x{symbolic_quantity(1)}")
      else:
       self.item(q,"phoenix_feather",1); got.append("Phoenix Feather x1")
     if random.random()<0.10:
      if symbolic_swarm:
       sr=q["symbolic_rewards"]; sr["inventory"]["mythic_token"]=sr["inventory"].get("mythic_token",0)+1
       got.append(f"Mythic Token x{symbolic_quantity(1)}")
      else:
       amount=swarm_multiplier
       self.item(q,"mythic_token",amount); got.append(f"Mythic Token x{display_number(amount)}")
     drops.append(f"<@{player_id}>: {', '.join(got) if got else 'no bonus drops'}")
    self.data["raids"].pop(g,None); self.flush()
    await ctx.reply(embed=self.embed(f"RAID CLEARED / {swarm_label(swarm_count)}x {b[0].upper()}",f"Defeated {swarm_label(swarm_count)} bosses. Rewards are multiplied by the selected swarm count.\n\n"+ "\n".join(drops)[:3800],discord.Color.green()),mention_author=False); return
   boss_hits=random.random() < {1:0.42,2:0.48,3:0.54,4:0.60}[phase]
   phase_multiplier={1:1.0,2:1.10,3:1.20,4:1.30}[phase]
   incoming=int(random.randint(*b[2])*phase_multiplier) if boss_hits else 0
   reduction=.35 if p["race"]=="gojo" and p["infinity_unlocked"] else race[2]
   incoming=max(1,int(incoming*(1-reduction))) if boss_hits else 0
   r["players"][uid]=max(0,r["players"][uid]-incoming); hp=r["players"][uid]
   alive2=[u for u in r["turns"] if r["players"].get(u,0)>0]
   if alive2:
    old=r["turns"].index(uid); seq=r["turns"][old+1:]+r["turns"][:old]; nxt=next((u for u in seq if r["players"].get(u,0)>0),None); r["turn"]=alive2.index(nxt) if nxt else 0; nextline=phase_line+f"\nNext turn: <@{nxt}>"
   else: self.data["raids"].pop(g,None); nextline=phase_line+"\nThe party has fallen."
   self.flush()
  count=r.get("swarm_count",1)
  target_line=f" every one of {swarm_label(count)} bosses" if count != 1 else ""
  e=self.embed("TURN RESOLVED",f"{ctx.author.mention} used {action} with {c[0]} for {display_number(damage)} damage to{target_line or ' the boss'}.\nTotal damage dealt: {total_damage_label}.\n{b[0]} retaliates for {incoming} damage. Your HP: {hp}/250.{nextline}")
  if g in self.data["raids"]: e.add_field(name="Boss vitality",value=f"{display_number(self.data['raids'][g]['hp'])} / {display_number(r['max_hp'])} HP per boss · {swarm_label(count)} remaining",inline=False)
  await ctx.reply(embed=e,mention_author=False)
 @commands.command(name="skills")
 async def skills(self,ctx):
  p=self.p(ctx.author.id); c=CHARACTERS[p["character"]]; unlocked=c[5] in p["unlocked"] or(p["race"]=="vessel" and p["character"]=="sukuna")
  await ctx.reply(embed=self.embed("TECHNIQUE RECORD",f"{c[0]} · {c[4]}\nDamage: {c[6][0]}–{c[6][1]}\nCost: {c[7]} points\nStatus: {'Unlocked' if unlocked else 'Locked'}"),mention_author=False)
 @commands.command(name="unlock")
 async def unlock(self,ctx,*,skill):
  p=self.p(ctx.author.id); c=CHARACTERS[p["character"]]; key=c[5]
  if skill.lower().strip()!=key: await ctx.reply(embed=self.embed("UNKNOWN SKILL",f"Your character uses {key}."),mention_author=False); return
  if key in p["unlocked"] or(p["race"]=="vessel" and p["character"]=="sukuna"): await ctx.reply(embed=self.embed("ALREADY UNLOCKED","This skill is already available."),mention_author=False); return
  if p["points"]<c[7]:
   sr=p["symbolic_rewards"]
   if sr["points"]<=sr["points_spent"]: await ctx.reply(embed=self.embed("NOT ENOUGH POINTS",f"You need {c[7]} points."),mention_author=False); return
   sr["points_spent"]+=c[7]-p["points"]; p["points"]=0
  else: p["points"]-=c[7]
  p["unlocked"].append(key); self.flush()
  await ctx.reply(embed=self.embed("SKILL UNLOCKED",c[4]+" is now available."),mention_author=False)
 @commands.command(name="inventory",aliases=["inv","bag"])
 async def inventory(self,ctx):
  p=self.p(ctx.author.id)
  lines=[f"{ITEMS.get(k,k)} x{display_number(v)}" for k,v in sorted(p["inventory"].items()) if v>0]
  sr=p["symbolic_rewards"]
  for k,v in sorted(sr["inventory"].items()):
   if v>0: lines.append(f"{ITEMS.get(k,k)} x{symbolic_quantity(v,sr['inventory_spent'].get(k,0))}")
  if not lines: lines=["Your inventory is empty."]
  e=self.embed("INVENTORY","\n".join(lines)[:4000])
  six=p["inventory"].get("six_eyes",0); fingers=p["inventory"].get("cursed_fingers",0)
  six_label=symbolic_quantity(sr["inventory"]["six_eyes"],sr['inventory_spent'].get("six_eyes",0)) if sr["inventory"].get("six_eyes",0) else display_number(six)
  finger_label=symbolic_quantity(sr["inventory"]["cursed_fingers"],sr['inventory_spent'].get("cursed_fingers",0)) if sr["inventory"].get("cursed_fingers",0) else display_number(fingers)
  e.add_field(name="Awakening progress",value=f"Six Eyes: {six_label}/6\nCursed Fingers: {finger_label}/20\nRace: {RACES[p['race']][0]}",inline=False)
  await ctx.reply(embed=e,mention_author=False)
 @commands.command(name="eat",aliases=["consume"])
 async def eat(self,ctx,*,item):
  key=item.lower().strip().replace(" ","_"); p=self.p(ctx.author.id)
  if key in {"six_eye","six_eyes"}:
   if p["race"]!="gojo" or not self.has_item(p,"six_eyes",6) or p["six_eyes_unlocked"]: await ctx.reply(embed=self.embed("AWAKENING UNAVAILABLE","You need Gojo Clan and 6 Six Eyes. You can only awaken once."),mention_author=False); return
   self.consume_item(p,"six_eyes",6); p["six_eyes_unlocked"]=True; p["infinity_unlocked"]=True; self.flush()
   await ctx.reply(embed=self.embed("LIMITLESS AWAKENED","Infinity and Six Eyes unlocked. Gojo Clan gains +20% damage and 35% damage reduction."),mention_author=False); return
  if key in {"cursed_finger","cursed_fingers","fingers"}:
   if p["race"]!="vessel" or not self.has_item(p,"cursed_fingers",20) or p["sukuna_race_unlocked"]: await ctx.reply(embed=self.embed("AWAKENING UNAVAILABLE","You need Vessel and 20 Cursed Fingers. This awakening can only be unlocked once."),mention_author=False); return
   self.consume_item(p,"cursed_fingers",20); p["sukuna_race_unlocked"]=True; p["race"]="sukuna"; self.flush()
   await ctx.reply(embed=self.embed("KING OF CURSES AWAKENED","20 fingers consumed. Secret race unlocked and equipped: +25% damage and 15% damage reduction."),mention_author=False); return
  await ctx.reply(embed=self.embed("CANNOT CONSUME","That item has no consumption effect."),mention_author=False)
 @commands.command(name="use")
 async def use_item(self,ctx,*,item):
  key=item.lower().strip().replace(" ","_")
  if key not in {"phoenix_feather","phoenix"}:
   await ctx.reply(embed=self.embed("ITEM NOT USABLE","Phoenix Feathers can revive you during an active raid."),mention_author=False); return
  g=str(ctx.guild.id) if ctx.guild else ""
  async with self.lock:
   r=self.data["raids"].get(g)
   uid=str(ctx.author.id); p=self.p(ctx.author.id)
   if not r or uid not in r["players"] or r["players"][uid]>0:
    await ctx.reply(embed=self.embed("CANNOT USE","You must be a defeated party member in an active raid."),mention_author=False); return
   if not self.has_item(p,"phoenix_feather",1):
    await ctx.reply(embed=self.embed("ITEM MISSING","You need a Phoenix Feather."),mention_author=False); return
   self.consume_item(p,"phoenix_feather",1); r["players"][uid]=150; self.flush()
  await ctx.reply(embed=self.embed("PHOENIX REVIVAL","Phoenix Feather consumed. You have returned with 150 HP."),mention_author=False)

 @commands.command(name="stats",aliases=["me"])
 async def stats(self,ctx,member:discord.Member=None):
  member=member or ctx.author; p=self.p(member.id); c=CHARACTERS[p["character"]]
  sr=p["symbolic_rewards"]
  symbolic_lines=[]
  if sr["xp"]: symbolic_lines.append(f"Symbolic XP: {symbolic_quantity(sr['xp'])} (stored separately from level progression)")
  if sr["points"]: symbolic_lines.append(f"Symbolic skill points: {symbolic_quantity(sr['points'],sr['points_spent'])}")
  if sr["wins"]: symbolic_lines.append(f"Symbolic victories: {symbolic_quantity(sr['wins'])}")
  if sr["damage"]: symbolic_lines.append(f"Symbolic damage: {symbolic_quantity(sr['damage'])}")
  equipped_title=p.get("equipped_title")
  title_name={"rookie":"Rookie","slayer":"Boss Slayer","conqueror":"Conqueror","calamity":"Calamity","limitless":"Limitless","king_of_curses":"King of Curses"}.get(equipped_title,"None")
  desc=(f"Title: {title_name}\nCharacter: {c[0]}\nRace: {RACES[p['race']][0]}\nLevel: {display_number(p['level'])}\nXP: {display_number(p['xp'])} / {display_number(p['level']*250)}\nSkill points: {display_number(p['points'])}\nVictories: {display_number(p['wins'])}\nTotal damage: {display_number(p['damage'])}" + ("\n" + "\n".join(symbolic_lines) if symbolic_lines else ""))
  e=self.embed("ADVENTURER PROFILE",desc[:4000])
  e.set_thumbnail(url=member.display_avatar.url); await ctx.reply(embed=e,mention_author=False)
 @commands.command(name="leaderboard",aliases=["top"])
 async def leaderboard(self,ctx):
  top=sorted(self.data["profiles"].items(),key=lambda x:(x[1].get("symbolic_rewards",{}).get("xp",0)>0,x[1].get("level",1),x[1].get("xp",0)),reverse=True)[:10]
  lines=[f"{i}. <@{uid}> · Level {display_number(p['level'])} · {display_number(p['xp'])} XP" for i,(uid,p) in enumerate(top,1)]
  await ctx.reply(embed=self.embed("ADVENTURER RANKINGS","\n".join(lines) or "No players yet."),mention_author=False)

 @commands.command(name="createweapon")
 @commands.is_owner()
 async def createweapon(self,ctx):
  e=self.embed("CUSTOM WEAPON FORGE","Open the builder to define a weapon name, description, basic damage and ability damage. Created weapons are stored in the JSON database.")
  await ctx.reply(embed=e,view=WeaponBuilderView(self,ctx.author.id),mention_author=False)
 @commands.group(name="weapon",invoke_without_command=True)
 async def weapon(self,ctx):
  await ctx.reply(embed=self.embed("WEAPON ARCHIVE","Use ,weapon list or ,weapon equip <key>."),mention_author=False)
 @weapon.command(name="list")
 async def weapon_list(self,ctx):
  custom=self.data.get("custom_weapons",{})
  if not custom: await ctx.reply(embed=self.embed("WEAPON ARCHIVE","No custom weapons have been forged yet."),mention_author=False); return
  e=self.embed("CUSTOM WEAPON ARCHIVE")
  for key,w in custom.items():
   e.add_field(name=f"{w['name']} / {key}",value=f"{w['damage'][0]}-{w['damage'][1]} basic damage\n{w['ability']}: {w['ability_damage'][0]}-{w['ability_damage'][1]}\n{w.get('description','')}",inline=False)
  await ctx.reply(embed=e,mention_author=False)
 @weapon.command(name="equip")
 async def weapon_equip(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_"); p=self.p(ctx.author.id)
  if key not in self.data.get("custom_weapons",{}):
   await ctx.reply(embed=self.embed("WEAPON NOT FOUND","Check ,weapon list for available custom weapons."),mention_author=False); return
  p["weapon"]=key; self.flush()
  await ctx.reply(embed=self.embed("WEAPON EQUIPPED",f"{self.data['custom_weapons'][key]['name']} is now equipped. Use ,attack or ,attack <ability name>."),mention_author=False)
 @weapon.command(name="unequip")
 async def weapon_unequip(self,ctx):
  p=self.p(ctx.author.id); p["weapon"]=None; self.flush()
  await ctx.reply(embed=self.embed("WEAPON UNEQUIPPED","Your character's standard attacks are active again."),mention_author=False)

 @commands.command(name="setdamage")
 @commands.is_owner()
 async def setdamage(self,ctx,amount:str):
  p=self.p(ctx.author.id)
  if not p.get("weapon") or p["weapon"] not in self.data.get("custom_weapons",{}):
   await ctx.reply(embed=self.embed("NO CUSTOM WEAPON EQUIPPED","Equip your custom weapon first with ,weapon equip <key>."),mention_author=False); return
  if amount.lower() in {"off","reset","none"}:
   p["weapon_damage_override"]=None; self.flush()
   await ctx.reply(embed=self.embed("WEAPON DAMAGE RESET",f"{self.data['custom_weapons'][p['weapon']]['name']} is back to its normal damage ranges."),mention_author=False); return
  if amount.lower() == "googolplex":
   p["weapon_damage_override"]="googolplex"; self.flush()
   await ctx.reply(embed=self.embed("WEAPON DAMAGE UPDATED","Your equipped weapon now uses googolplex damage. It hits for the boss's remaining HP."),mention_author=False); return
  try: value=int(amount.replace(",",""))
  except ValueError:
   await ctx.reply(embed=self.embed("INVALID DAMAGE","Use ,setdamage <amount> or ,setdamage off."),mention_author=False); return
  if not 1<=value<=10**100:
   await ctx.reply(embed=self.embed("INVALID DAMAGE","Damage must be a positive whole number."),mention_author=False); return
  p["weapon_damage_override"]=value; self.flush()
  await ctx.reply(embed=self.embed("WEAPON DAMAGE UPDATED",f"Your equipped weapon **{self.data['custom_weapons'][p['weapon']]['name']}** now deals **{value:,}** damage on every basic attack and ability. This only affects your profile."),mention_author=False)

 @commands.command(name="giveitem")
 @commands.is_owner()
 async def giveitem(self,ctx,member:discord.User,item:str,amount:int=1):
  key=item.lower().strip().replace(" ","_")
  if key not in ITEMS or not 1<=amount<=100000: await ctx.reply(embed=self.embed("INVALID ITEM","Use a listed item key and an amount from 1 to 100000."),mention_author=False); return
  p=self.p(member.id); self.item(p,key,amount); self.flush()
  await ctx.reply(embed=self.embed("OWNER ITEM GRANT",f"Granted {ITEMS[key]} x{amount} to {member.mention}."),mention_author=False)
 @commands.command(name="addxp")
 @commands.is_owner()
 async def addxp(self,ctx,member:discord.User,amount:int):
  if not 0<=amount<=100000000: await ctx.reply(embed=self.embed("INVALID XP","Amount must be 0 to 100000000."),mention_author=False); return
  p=self.p(member.id); p["xp"]+=amount
  apply_level_ups(p)
  self.flush(); await ctx.reply(embed=self.embed("OWNER XP GRANT",f"Added {amount:,} XP. New level: {p['level']}."),mention_author=False)
 @commands.command(name="setlevel")
 @commands.is_owner()
 async def setlevel(self,ctx,member:discord.User,level:int):
  if not 1<=level<=10000: await ctx.reply(embed=self.embed("INVALID LEVEL","Choose 1 to 10000."),mention_author=False); return
  p=self.p(member.id); p["level"]=level; p["xp"]=0; self.flush()
  await ctx.reply(embed=self.embed("OWNER LEVEL UPDATE",f"{member.mention} is now level {level}."),mention_author=False)
 @commands.command(name="addpoints")
 @commands.is_owner()
 async def addpoints(self,ctx,member:discord.User,amount:int):
  if not 0<=amount<=100000: await ctx.reply(embed=self.embed("INVALID AMOUNT","Skill points must be 0 to 100000."),mention_author=False); return
  p=self.p(member.id); p["points"]+=amount; self.flush()
  await ctx.reply(embed=self.embed("OWNER POINT GRANT",f"Added {amount} skill points to {member.mention}."),mention_author=False)
 @commands.command(name="setcharacter")
 @commands.is_owner()
 async def setcharacter(self,ctx,member:discord.User,*,character:str):
  key=character.lower().strip().replace(" ","_")
  if key not in CHARACTERS: await ctx.reply(embed=self.embed("INVALID CHARACTER","Use a character key from ,characters."),mention_author=False); return
  p=self.p(member.id); p["character"]=key; self.flush()
  await ctx.reply(embed=self.embed("OWNER CHARACTER UPDATE",f"{member.mention} now uses {CHARACTERS[key][0]}."),mention_author=False)
 @commands.command(name="setrace")
 @commands.is_owner()
 async def setrace(self,ctx,member:discord.User,*,race:str):
  key=race.lower().strip().replace(" ","_"); p=self.p(member.id)
  if key not in RACES: await ctx.reply(embed=self.embed("INVALID RACE","Use a key shown in ,races."),mention_author=False); return
  if key=="sukuna": p["sukuna_race_unlocked"]=True
  p["race"]=key; self.flush(); await ctx.reply(embed=self.embed("OWNER RACE UPDATE",f"{member.mention} is now {RACES[key][0]}."),mention_author=False)
 @commands.command(name="resetprofile")
 @commands.is_owner()
 async def resetprofile(self,ctx,member:discord.User):
  self.data["profiles"][str(member.id)]=json.loads(json.dumps(DEFAULT)); self.flush()
  await ctx.reply(embed=self.embed("PROFILE RESET",f"Reset {member.mention}'s adventure profile."),mention_author=False)
 @commands.command(name="gamedb")
 @commands.is_owner()
 async def gamedb(self,ctx):
  await ctx.reply(embed=self.embed("JSON DATABASE",f"Profiles: {len(self.data['profiles'])}\nActive raids: {len(self.data['raids'])}\nFile: {DB_FILE}"),mention_author=False)
 async def cog_command_error(self,ctx,error):
  if isinstance(error,commands.NotOwner): await ctx.reply(embed=self.embed("ACCESS DENIED","This command is restricted to BOT_OWNER_ID.",discord.Color.red()),mention_author=False)
  elif isinstance(error,commands.CommandOnCooldown): await ctx.reply(embed=self.embed("COOLDOWN","Wait one second before attacking again.",discord.Color.orange()),mention_author=False)
  else: raise error

async def setup(bot):
 await bot.add_cog(Adventure(bot))
