import asyncio, json, os, random, sqlite3, tempfile
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
DEFAULT = {"xp":0,"level":1,"points":0,"character":"sukuna","weapon":None,"unlocked":[],"race":"human","inventory":{},"six_eyes_unlocked":False,"infinity_unlocked":False,"sukuna_race_unlocked":False,"wins":0,"damage":0}

def save(data):
 ROOT.mkdir(parents=True,exist_ok=True)
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
  return p
 def flush(self): save(self.data)
 def embed(self,title,desc="",color=None):
  e=discord.Embed(title=title,description=desc,color=color or discord.Color.from_rgb(48,61,82)); e.set_footer(text="PEAK  /  ANIME CHRONICLES"); return e
 def item(self,p,key,n):
  p["inventory"][key]=max(0,p["inventory"].get(key,0)+n)
  if not p["inventory"][key]: p["inventory"].pop(key,None)

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
  await ctx.reply(embed=self.embed("RAID COMMANDS",",bosses · ,boss challenge <key> · ,boss summon <key> <count> · ,boss status · ,join · ,attack [skill]"),mention_author=False)
 @boss.command(name="summon")
 @commands.guild_only()
 @commands.is_owner()
 async def summon(self,ctx,key:str,count:int):
  key=key.lower().strip().replace(" ","_")
  if key not in BOSSES:
   await ctx.reply(embed=self.embed("UNKNOWN TARGET","Use ,bosses to view available bosses."),mention_author=False); return
  if not 1<=count<=1000:
   await ctx.reply(embed=self.embed("INVALID COUNT","You can summon between 1 and 1000 bosses."),mention_author=False); return
  async with self.lock:
   g=str(ctx.guild.id)
   if g in self.data["raids"]:
    await ctx.reply(embed=self.embed("RAID ACTIVE","Finish the current raid first."),mention_author=False); return
   b=BOSSES[key]
   self.data["raids"][g]={"boss":key,"hp":b[1],"max_hp":b[1],"swarm_count":count,"players":{str(ctx.author.id):250},"turns":[str(ctx.author.id)],"turn":0,"damage":{}}
   self.flush()
  await ctx.reply(embed=self.embed("BOSS SWARM SUMMONED",f"Summoned **{count:,} {b[0]}**. Each attack damages every living boss for the same amount.\nPer-boss HP: {b[1]:,}\nFirst turn: {ctx.author.mention}. Others can use ,join."),mention_author=False)
 @boss.command(name="challenge")
 @commands.guild_only()
 async def challenge(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_")
  if key not in BOSSES: await ctx.reply(embed=self.embed("UNKNOWN TARGET","Use ,bosses to view the raid register."),mention_author=False); return
  async with self.lock:
   g=str(ctx.guild.id)
   if g in self.data["raids"]: await ctx.reply(embed=self.embed("RAID ACTIVE","Finish the current raid first."),mention_author=False); return
   b=BOSSES[key]; self.data["raids"][g]={"boss":key,"hp":b[1],"max_hp":b[1],"players":{str(ctx.author.id):250},"turns":[str(ctx.author.id)],"turn":0,"damage":{}}
   self.flush()
  await ctx.reply(embed=self.embed(f"RAID STARTED / {b[0].upper()}",f"{b[1]:,} HP. First turn: {ctx.author.mention}. Others can use ,join."),mention_author=False)
 @commands.command(name="join")
 @commands.guild_only()
 async def join(self,ctx):
  async with self.lock:
   r=self.data["raids"].get(str(ctx.guild.id)); uid=str(ctx.author.id)
   if not r: await ctx.reply(embed=self.embed("NO RAID","Start a raid with ,boss challenge <key>."),mention_author=False); return
   if uid in r["players"]: await ctx.reply(embed=self.embed("ALREADY JOINED","You are already in this raid."),mention_author=False); return
   r["players"][uid]=250; r["turns"].append(uid); self.flush()
  await ctx.reply(embed=self.embed("PLAYER JOINED",f"{ctx.author.mention} entered with 250 HP."),mention_author=False)
 @boss.command(name="status")
 @commands.guild_only()
 async def status(self,ctx):
  r=self.data["raids"].get(str(ctx.guild.id))
  if not r: await ctx.reply(embed=self.embed("NO RAID","There is no active raid."),mention_author=False); return
  b=BOSSES[r["boss"]]; alive=[u for u in r["turns"] if r["players"].get(u,0)>0]; current=alive[r["turn"]%len(alive)] if alive else None
  count=r.get("swarm_count",1)
  title=f"{count:,}x {b[0].upper()}" if count>1 else b[0].upper()
  e=self.embed(title,f"{r['hp']:,} / {r['max_hp']:,} HP per boss · {count:,} remaining"); e.add_field(name="Current turn",value=f"<@{current}>" if current else "None")
  e.add_field(name="Party",value="\n".join(f"<@{u}> · {hp}/250 HP" for u,hp in r["players"].items())[:1024],inline=False)
  await ctx.reply(embed=e,mention_author=False)
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
   else:
    skill=c[5]
    if ability:
     if ability.lower().strip()!=skill or (skill not in p["unlocked"] and not(p["race"]=="vessel" and p["character"]=="sukuna")):
      await ctx.reply(embed=self.embed("SKILL LOCKED",f"Unlock {skill} with ,unlock {skill}. Vessel gets Sukuna's skill free."),mention_author=False); return
     damage=random.randint(*c[6]); action=c[4]
    else: damage=random.randint(*c[3]); action="Basic strike"
   race=RACES[p["race"]]; mult=1.20 if p["race"]=="gojo" and p["six_eyes_unlocked"] else race[1]
   damage=min(r["hp"],max(1,int(damage*mult))); r["hp"]-=damage
   swarm_count=r.get("swarm_count",1)
   total_damage=damage*swarm_count
   r["damage"][uid]=r["damage"].get(uid,0)+total_damage; p["damage"]+=total_damage
   b=BOSSES[r["boss"]]
   if r["hp"]<=0:
    drops=[]
    for player_id in list(r["players"]):
     q=self.p(int(player_id)); q["xp"]+=b[3]*swarm_count+r["damage"].get(player_id,0)//4; q["points"]+=swarm_count; q["wins"]+=swarm_count
     while q["xp"]>=q["level"]*250: q["xp"]-=q["level"]*250; q["level"]+=1; q["points"]+=1
     got=[]
     for item,limits in b[4].items():
      amount=random.randint(*limits)*swarm_count
      self.item(q,item,amount); got.append(f"{ITEMS.get(item,item)} x{amount}")
     if random.random()<0.10:
      amount=swarm_count
      self.item(q,"mythic_token",amount); got.append(f"Mythic Token x{amount}")
     drops.append(f"<@{player_id}>: {', '.join(got) if got else 'no bonus drops'}")
    self.data["raids"].pop(g,None); self.flush()
    await ctx.reply(embed=self.embed(f"RAID CLEARED / {swarm_count:,}x {b[0].upper()}",f"Defeated {swarm_count:,} bosses. Rewards were multiplied by the boss count.\n\n"+ "\n".join(drops),discord.Color.green()),mention_author=False); return
   boss_hits=random.random()<0.72
   incoming=random.randint(*b[2]) if boss_hits else 0
   reduction=.35 if p["race"]=="gojo" and p["infinity_unlocked"] else race[2]
   incoming=max(1,int(incoming*(1-reduction))) if boss_hits else 0
   r["players"][uid]=max(0,r["players"][uid]-incoming); hp=r["players"][uid]
   alive2=[u for u in r["turns"] if r["players"].get(u,0)>0]
   if alive2:
    old=r["turns"].index(uid); seq=r["turns"][old+1:]+r["turns"][:old]; nxt=next((u for u in seq if r["players"].get(u,0)>0),None); r["turn"]=alive2.index(nxt) if nxt else 0; nextline=f"\nNext turn: <@{nxt}>"
   else: self.data["raids"].pop(g,None); nextline="\nThe party has fallen."
   self.flush()
  count=r.get("swarm_count",1)
  target_line=f" every one of {count:,} bosses" if count>1 else ""
  e=self.embed("TURN RESOLVED",f"{ctx.author.mention} used {action} with {c[0]} for {damage:,} damage to{target_line or ' the boss'}.\nTotal damage dealt: {total_damage:,}.\n{b[0]} retaliates for {incoming} damage. Your HP: {hp}/250.{nextline}")
  if g in self.data["raids"]: e.add_field(name="Boss vitality",value=f"{self.data['raids'][g]['hp']:,} / {r['max_hp']:,} HP per boss · {count:,} remaining",inline=False)
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
  if p["points"]<c[7]: await ctx.reply(embed=self.embed("NOT ENOUGH POINTS",f"You need {c[7]} points."),mention_author=False); return
  p["points"]-=c[7]; p["unlocked"].append(key); self.flush()
  await ctx.reply(embed=self.embed("SKILL UNLOCKED",c[4]+" is now available."),mention_author=False)
 @commands.command(name="inventory",aliases=["inv","bag"])
 async def inventory(self,ctx):
  p=self.p(ctx.author.id); lines=[f"{ITEMS.get(k,k)} x{v}" for k,v in sorted(p["inventory"].items()) if v>0] or ["Your inventory is empty."]
  e=self.embed("INVENTORY","\n".join(lines)); e.add_field(name="Awakening progress",value=f"Six Eyes: {p['inventory'].get('six_eyes',0)}/6\nCursed Fingers: {p['inventory'].get('cursed_fingers',0)}/20\nRace: {RACES[p['race']][0]}",inline=False)
  await ctx.reply(embed=e,mention_author=False)
 @commands.command(name="eat",aliases=["consume"])
 async def eat(self,ctx,*,item):
  key=item.lower().strip().replace(" ","_"); p=self.p(ctx.author.id)
  if key in {"six_eye","six_eyes"}:
   if p["race"]!="gojo" or p["inventory"].get("six_eyes",0)<6 or p["six_eyes_unlocked"]: await ctx.reply(embed=self.embed("AWAKENING UNAVAILABLE","You need Gojo Clan and 6 Six Eyes. You can only awaken once."),mention_author=False); return
   self.item(p,"six_eyes",-6); p["six_eyes_unlocked"]=True; p["infinity_unlocked"]=True; self.flush()
   await ctx.reply(embed=self.embed("LIMITLESS AWAKENED","Infinity and Six Eyes unlocked. Gojo Clan gains +20% damage and 35% damage reduction."),mention_author=False); return
  if key in {"cursed_finger","cursed_fingers","fingers"}:
   if p["race"]!="vessel" or p["inventory"].get("cursed_fingers",0)<20 or p["sukuna_race_unlocked"]: await ctx.reply(embed=self.embed("AWAKENING UNAVAILABLE","You need Vessel and 20 Cursed Fingers. This awakening can only be unlocked once."),mention_author=False); return
   self.item(p,"cursed_fingers",-20); p["sukuna_race_unlocked"]=True; p["race"]="sukuna"; self.flush()
   await ctx.reply(embed=self.embed("KING OF CURSES AWAKENED","20 fingers consumed. Secret race unlocked and equipped: +25% damage and 15% damage reduction."),mention_author=False); return
  await ctx.reply(embed=self.embed("CANNOT CONSUME","That item has no consumption effect."),mention_author=False)
 @commands.command(name="stats",aliases=["me"])
 async def stats(self,ctx,member:discord.Member=None):
  member=member or ctx.author; p=self.p(member.id); c=CHARACTERS[p["character"]]
  e=self.embed("ADVENTURER PROFILE",f"Character: {c[0]}\nRace: {RACES[p['race']][0]}\nLevel: {p['level']} · XP: {p['xp']}/{p['level']*250}\nSkill points: {p['points']}\nVictories: {p['wins']}\nTotal damage: {p['damage']:,}")
  e.set_thumbnail(url=member.display_avatar.url); await ctx.reply(embed=e,mention_author=False)
 @commands.command(name="leaderboard",aliases=["top"])
 async def leaderboard(self,ctx):
  top=sorted(self.data["profiles"].items(),key=lambda x:(x[1].get("level",1),x[1].get("xp",0)),reverse=True)[:10]
  lines=[f"{i}. <@{uid}> · Level {p['level']} · {p['xp']} XP" for i,(uid,p) in enumerate(top,1)]
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
  while p["xp"]>=p["level"]*250: p["xp"]-=p["level"]*250; p["level"]+=1; p["points"]+=1
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
