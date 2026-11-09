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
 # Starter encounters from several anime worlds. These are intentionally weaker
 # than the original raid roster so new players have a clear progression path.
 "bandit":("East Blue Bandit",220,(5,9),45,{"bandit_badge":(1,2),"basic_potion":(1,2)}),
 "buggy":("Buggy the Clown",360,(7,12),75,{"buggy_emblem":(1,2),"devil_fruit_shard":(1,1)}),
 "mizuki":("Mizuki",480,(8,14),100,{"rogue_ninja_headband":(1,2),"chakra_crystal":(1,1)}),
 "fishbone_d":("Fishbone D",620,(10,16),130,{"hollow_fragment":(1,2),"soul_fragment":(1,1)}),
 "hand_demon":("Hand Demon",780,(12,19),165,{"demon_blood":(1,2),"nightmare_ash":(1,1)}),
 "sludge_villain":("Sludge Villain",920,(14,22),200,{"quirk_residue":(1,2),"healing_potion":(1,1)}),
 "raditz":("Raditz",1150,(17,26),250,{"saiyan_armor":(1,2),"zenkai_cell":(1,1)}),
 "low_rank_curse":("Grade 2 Cursed Spirit",1350,(19,29),290,{"cursed_ash":(1,2),"soul_fragment":(1,1)}),
 "mahito":("Mahito",1600,(28,46),350,{"cursed_ash":(1,3),"cursed_fingers":(1,2),"transfigured_soul":(1,2),"idle_transfiguration":(1,1),"soul_fragment":(1,3),"black_flash_residue":(1,2),"void_ore":(1,2),"healing_potion":(1,2)}),
 "doflamingo":("Donquixote Doflamingo",2800,(38,62),650,{"string_core":(1,3),"devil_fruit_shard":(1,2),"birdcage_thread":(1,2),"celestial_blood":(1,1),"ito_essence":(1,2),"flamingo_feather":(1,3),"starsteel":(1,2)}),
 "madara":("Madara Uchiha",4700,(52,82),1200,{"six_paths_essence":(1,2),"chakra_crystal":(1,3),"susanoo_fragment":(1,2),"rinnegan_shard":(1,1),"god_tree_seed":(1,2),"uchiha_relic":(1,3),"awakening_crystal":(1,2)}),
 "frieza":("Frieza",7000,(65,98),1900,{"dragon_ball":(1,2),"cosmic_core":(1,2),"frozen_pod":(1,3),"saiyan_armor":(1,2),"tyrant_emblem":(1,1),"zenkai_cell":(1,2),"dragon_scale":(1,3),"battle_tonic":(1,2)}),
 "gojo":("Satoru Gojo",2200,(32,52),550,{"six_eyes":(1,1),"limitless_core":(1,2),"blue_orb":(1,2),"red_orb":(1,2),"hollow_purple_shard":(1,1),"blindfold_fabric":(1,3),"focus_elixir":(1,2)}),
 "sukuna":("Ryomen Sukuna",5600,(58,92),1650,{"cursed_fingers":(1,3),"cursed_ash":(1,2),"sukuna_relic":(1,1),"malevolent_essence":(1,2),"shrine_fragment":(1,2),"king_of_curses_seal":(1,1),"spirit_silk":(1,2)}),
 "muzan":("Muzan Kibutsuji",3900,(48,76),1050,{"demon_blood":(1,2),"sunsteel":(1,2),"blue_spider_lily":(1,1),"flesh_core":(1,3),"demon_cell":(1,2),"nightmare_ash":(1,2),"ancient_core":(1,1)}),
 "meruem":("Meruem",6200,(62,94),1800,{"chimera_essence":(1,2),"royal_core":(1,1),"nen_crystal":(1,3),"chimera_scale":(1,2),"royal_guard_token":(1,1),"kingly_aura":(1,2),"celestial_dust":(1,2)}),
 "all_for_one":("All For One",5100,(55,86),1450,{"quirk_catalyst":(1,2),"all_for_one_core":(1,1),"stolen_quirk_shard":(1,3),"nomu_tissue":(1,2),"alliance_emblem":(1,1),"impact_relic":(1,2),"dimension_key":(1,1)}),
 "zeref":("Zeref",8200,(72,108),2400,{"ether_core":(1,2),"curse_book":(1,1),"fairy_heart_shard":(1,2),"black_magic_ash":(1,3),"immortality_seal":(1,1),"time_rift_fragment":(1,2),"dimension_key":(1,1),"awakening_crystal":(1,2)}),
 "kenpachi":("Kenpachi Zaraki",9600,(78,118),2800,{"ether_core":(2,4),"soul_fragment":(2,5),"spirit_silk":(1,3),"zanpakuto_core":(1,2)}),
 "kaido":("Kaido",12500,(92,140),3600,{"dragon_scale":(2,5),"dragon_ball":(2,4),"cosmic_core":(2,4),"oni_horn":(1,2)}),
 "kaguya":("Kaguya Otsutsuki",14800,(105,158),4300,{"chakra_crystal":(2,5),"six_paths_essence":(2,4),"god_tree_seed":(1,3),"dimensional_eye":(1,2)}),
 "madara_six_paths":("Six Paths Madara",17200,(118,176),5100,{"uchiha_relic":(2,5),"rinnegan_shard":(1,3),"six_paths_essence":(2,5),"ten_tails_core":(1,2)}),
 "anti_spiral":("Anti-Spiral",24000,(145,210),7200,{"void_ore":(3,6),"ancient_core":(2,4),"time_rift_fragment":(2,5),"dimension_key":(1,3),"spiral_core":(1,2)}),
 "jogo":("Jogo",3000,(38,58),720,{"cursed_ash":(2,4),"soul_fragment":(1,2),"cursed_fingers":(1,1)}),
 "hanami":("Hanami",3100,(36,56),740,{"cursed_ash":(2,4),"soul_fragment":(1,2),"cursed_fingers":(1,1)}),
 "toji":("Toji Fushiguro",2800,(42,64),780,{"uchiha_relic":(1,2),"soul_fragment":(1,3),"cursed_fingers":(1,1)}),
 "jjk_sukuna":("Sukuna: King of Curses",5200,(62,94),1600,{"cursed_fingers":(2,4),"malevolent_essence":(1,3),"sukuna_relic":(1,2)}),
 "jjk_gojo":("Gojo: Honored One",4900,(58,90),1500,{"six_eyes":(1,2),"limitless_core":(1,3),"blue_orb":(1,2)}),
 "jjk_mahito":("Mahito: Soul Manipulator",4300,(54,82),1300,{"transfigured_soul":(2,4),"cursed_ash":(2,4),"soul_fragment":(2,3)}),
 "dio":("DIO",4200,(54,82),1250,{"dio_bone":(1,1),"dio_diary":(1,1),"green_baby":(1,1),"stand_arrow":(1,2)}),
 "pucci":("Enrico Pucci",4600,(58,86),1400,{"dio_bone":(1,1),"dio_diary":(1,1),"green_baby":(1,1),"stand_arrow":(1,2)}),
 "diavolo":("Diavolo",4400,(56,84),1350,{"dio_bone":(1,1),"dio_diary":(1,1),"green_baby":(1,1),"stand_arrow":(1,2)}),
 "kira":("Yoshikage Kira",3900,(50,78),1150,{"dio_bone":(1,1),"dio_diary":(1,1),"green_baby":(1,1),"stand_arrow":(1,2)}),
 "dio_vampire":("DIO Vampire",5000,(64,96),1550,{"dio_bone":(1,2),"dio_diary":(1,1),"green_baby":(1,1),"stand_arrow":(1,2)}),
 "itachi":("Itachi Uchiha",4100,(52,80),1200,{"uchiha_relic":(2,4),"chakra_crystal":(2,4),"six_paths_essence":(1,1)}),
 "hashirama":("Hashirama Senju",4700,(58,88),1450,{"chakra_crystal":(3,5),"god_tree_seed":(1,2),"uchiha_relic":(1,2)}),
 "momoshiki":("Momoshiki Otsutsuki",6200,(72,108),1900,{"dimensional_eye":(1,2),"chakra_crystal":(3,5),"six_paths_essence":(1,3)}),
 "isshiki":("Isshiki Otsutsuki",6800,(78,116),2200,{"dimensional_eye":(2,3),"chakra_crystal":(3,5),"ten_tails_core":(1,2)}),
 "naruto_six_paths":("Naruto: Six Paths",5600,(68,102),1750,{"chakra_crystal":(2,4),"six_paths_essence":(1,3),"ten_tails_core":(1,1)}),
}
ITEMS = {k:k.replace("_"," ").title() for b in BOSSES.values() for k in b[4]}
ITEMS.update({"limitless_core":"Limitless Core","phoenix_feather":"Phoenix Feather","mythic_token":"Mythic Token"})

ITEMS.update({"void_ore":"Void Ore","starsteel":"Starsteel","dragon_scale":"Dragon Scale","spirit_silk":"Spirit Silk","ancient_core":"Ancient Core","dimension_key":"Dimension Key","awakening_crystal":"Awakening Crystal","celestial_dust":"Celestial Dust","zanpakuto_core":"Zanpakuto Core","oni_horn":"Oni Horn","dimensional_eye":"Dimensional Eye","ten_tails_core":"Ten Tails Core","spiral_core":"Spiral Core","rift_crystal":"Rift Crystal","phoenix_ash":"Phoenix Ash","abyssal_pearl":"Abyssal Pearl"})
ITEMS.update({"jjk_key":"JJK Key","jojo_key":"JoJo Key","naruto_key":"Naruto Key","clan_token":"Clan Reroll","six_eyes":"Six Eyes","dio_bone":"Dio Bone","dio_diary":"Dio Diary","green_baby":"Green Baby","stand_arrow":"Stand Arrow","itachi_soul":"Itachi Soul","uchiha_soul":"Uchiha Soul","chakra_fruit":"Chakra Fruit","fruit_chest":"Fruit Chest","luffy_soul":"Luffy Soul","one_piece_soul":"One Piece Soul","imu_key":"IMU Key","joyboy_key":"Joyboy Key","katana":"Katana"})
WEAPON_RECIPES = {
 "cursed_katana":{"name":"Cursed Katana","damage":[125,175],"ability":"Cleave","ability_key":"cleave","ability_damage":[230,300],"description":"A blade tempered with cursed energy.","level":8,"materials":{"cursed_ash":12,"soul_fragment":8,"void_ore":3}},
 "sixfold_spear":{"name":"Sixfold Spear","damage":[160,215],"ability":"Blue Impact","ability_key":"blue_impact","ability_damage":[290,370],"description":"A spear that bends space.","level":15,"materials":{"limitless_core":2,"blue_orb":8,"starsteel":5}},
 "dragon_fang":{"name":"Dragon Fang","damage":[190,250],"ability":"Dragon Roar","ability_key":"dragon_roar","ability_damage":[350,440],"description":"A dragon-forged weapon.","level":22,"materials":{"dragon_ball":5,"cosmic_core":4,"dragon_scale":10}},
 "soul_reaper":{"name":"Soul Reaper","damage":[225,290],"ability":"Getsuga Breaker","ability_key":"getsuga_breaker","ability_damage":[410,520],"description":"A blade resonating with spiritual pressure.","level":30,"materials":{"soul_fragment":15,"ether_core":8,"spirit_silk":6}},
 "reality_edge":{"name":"Reality Edge","damage":[280,360],"ability":"Rift Rend","ability_key":"rift_rend","ability_damage":[520,680],"description":"Forged at the edge of a collapsing dimension.","level":40,"materials":{"time_rift_fragment":8,"void_ore":15,"ancient_core":3,"celestial_dust":10}},
 "stormfang":{"name":"Stormfang","damage":[310,390],"ability":"Thunder God Strike","ability_key":"thunder_god_strike","ability_damage":[580,720],"description":"A blade charged by a storm dragon.","level":45,"materials":{"dragon_scale":15,"oni_horn":5,"cosmic_core":10}},
 "zanpakuto_prime":{"name":"Zanpakuto Prime","damage":[350,430],"ability":"Bankai: Final Verdict","ability_key":"bankai_final_verdict","ability_damage":[650,820],"description":"A perfected soul-cutting blade.","level":50,"materials":{"zanpakuto_core":8,"ether_core":15,"spirit_silk":12}},
 "ten_tails_staff":{"name":"Ten Tails Staff","damage":[390,480],"ability":"Truth-Seeking Burst","ability_key":"truth_seeking_burst","ability_damage":[740,900],"description":"A staff formed from primordial chakra.","level":55,"materials":{"ten_tails_core":5,"dimensional_eye":5,"six_paths_essence":12}},
 "anti_spiral_edge":{"name":"Anti-Spiral Edge","damage":[480,600],"ability":"Infinity Big Bang","ability_key":"infinity_big_bang","ability_damage":[900,1150],"description":"A weapon forged beyond the final dimension.","level":65,"materials":{"spiral_core":8,"void_ore":25,"dimension_key":5,"time_rift_fragment":20}}
}
SKILL_TREE = {
 "black_flash_chain":{"name":"Black Flash Chain","cost":3,"multiplier":1.8,"level":5,"materials":{"black_flash_residue":3}},
 "domain_amplification":{"name":"Domain Amplification","cost":5,"multiplier":2.2,"level":12,"materials":{"cursed_ash":8,"malevolent_essence":2}},
 "chakra_surge":{"name":"Chakra Surge","cost":4,"multiplier":2.0,"level":10,"materials":{"chakra_crystal":6}},
 "conquerors_haki":{"name":"Conqueror's Haki","cost":6,"multiplier":2.5,"level":18,"materials":{"kingly_aura":3,"celestial_blood":2}},
 "final_getsuga":{"name":"Final Getsuga","cost":8,"multiplier":3.0,"level":25,"materials":{"ether_core":8,"soul_fragment":12}},
 "limit_breaker":{"name":"Limit Breaker","cost":10,"multiplier":3.5,"level":35,"materials":{"zenkai_cell":8,"cosmic_core":8,"awakening_crystal":2}},
 "thunder_god_strike":{"name":"Thunder God Strike","cost":12,"multiplier":3.8,"level":42,"materials":{"dragon_scale":8,"oni_horn":3}},
 "bankai_final_verdict":{"name":"Bankai: Final Verdict","cost":14,"multiplier":4.2,"level":48,"materials":{"zanpakuto_core":5,"ether_core":10}},
 "truth_seeking_burst":{"name":"Truth-Seeking Burst","cost":16,"multiplier":4.6,"level":55,"materials":{"ten_tails_core":3,"dimensional_eye":3}},
 "infinity_big_bang":{"name":"Infinity Big Bang","cost":20,"multiplier":5.0,"level":65,"materials":{"spiral_core":5,"void_ore":15,"dimension_key":3}}
}
DIMENSIONS = {
 "earth":{"name":"Earth","level":1,"wins":0,"materials":{},"bonus":1.0,"description":"The starting world."},
 "cursed_realm":{"name":"Cursed Realm","level":8,"wins":3,"materials":{"cursed_ash":8,"soul_fragment":5},"bonus":1.08,"description":"A realm saturated with cursed energy."},
 "ninja_world":{"name":"Ninja World","level":15,"wins":8,"materials":{"chakra_crystal":8,"uchiha_relic":2},"bonus":1.12,"description":"A world shaped by chakra."},
 "new_world":{"name":"New World","level":22,"wins":15,"materials":{"devil_fruit_shard":8,"string_core":8},"bonus":1.16,"description":"A dangerous sea ruled by pirates."},
 "soul_society":{"name":"Soul Society","level":30,"wins":25,"materials":{"ether_core":8,"soul_fragment":15},"bonus":1.20,"description":"A spiritual plane."},
 "dragon_world":{"name":"Dragon World","level":40,"wins":40,"materials":{"dragon_ball":8,"cosmic_core":12,"dragon_scale":5},"bonus":1.25,"description":"A cosmic battlefield."},
 "infinity_void":{"name":"Infinity Void","level":55,"wins":75,"materials":{"time_rift_fragment":15,"void_ore":20,"ancient_core":5,"dimension_key":1},"bonus":1.35,"description":"An endgame realm beyond ordinary space."},
 "demon_castle":{"name":"Demon Castle","level":28,"wins":20,"materials":{"demon_blood":15,"sunsteel":8,"nightmare_ash":8},"bonus":1.18,"description":"A fortress ruled by ancient demons."},
 "celestial_plane":{"name":"Celestial Plane","level":48,"wins":55,"materials":{"celestial_dust":20,"six_paths_essence":12,"dimensional_eye":2},"bonus":1.30,"description":"A realm suspended above mortal worlds."},
 "spiral_nexus":{"name":"Spiral Nexus","level":65,"wins":100,"materials":{"spiral_core":5,"void_ore":25,"dimension_key":4,"time_rift_fragment":15},"bonus":1.45,"description":"The final frontier where dimensions collapse."}
}

RACES = {
 "human":("Human",1.0,0.0,"Balanced starting race."),
 "gojo":("Gojo Clan",1.10,.10,"+10% damage and 10% damage reduction."),
 "saiyan":("Saiyan",1.15,0.0,"+15% damage."),
 "fishman":("Fish-Man",1.0,.20,"20% damage reduction."),
 "shinobi":("Shinobi",1.07,.08,"+7% damage and 8% damage reduction."),
 "curse":("Cursed Spirit",1.12,-.05,"+12% damage, takes 5% more damage."),
 "vessel":("Sukuna Vessel",1.12,0.0,"+12% damage; Sukuna's signature skill is free."),
 "sukuna":("King of Curses",1.25,.15,"Secret race: +25% damage and 15% damage reduction."),
 "sorcerer":("Sorcerer",1.18,-.02,"JJK bloodline: +18% damage, 2% less damage taken."),
 "cursed_race":("Cursed",1.22,-.05,"Cursed body: +22% damage, takes 5% less damage."),
 "uchiha":("Uchiha",1.30,.05,"Rare bloodline: +30% damage and 5% damage reduction."),
 "senju":("Senju",1.20,.04,"Vitality and chakra: +20% damage and 4% damage reduction."),
 "uzumaki":("Uzumaki",1.15,.03,"Strong life force: +15% damage and 3% damage reduction."),
 "fallen":("The Fallen",1.32,.06,"Mythic race: +32% damage and 6% damage reduction."),
}
CLANS = {
 "satoru":{"name":"Satoru","melee":0.50,"sword":0.50,"magic":1.50,"rarity":"0.5%"},
 "zenin":{"name":"Zenin","melee":1.00,"sword":1.00,"magic":0.0,"rarity":"0.5%"},
 "kamo":{"name":"Kamo","melee":1.50,"sword":0.0,"magic":0.50,"rarity":"0.5%"},
 "akatsuki":{"name":"Akatsuki","melee":1.00,"sword":0.70,"magic":0.50,"rarity":"0.1%"},
 "konoha":{"name":"Konoha","melee":0.50,"sword":0.70,"magic":1.00,"rarity":"0.1%"},
 "otogakure":{"name":"Otogakure","melee":0.0,"sword":0.70,"magic":0.50,"rarity":"3%"},
 "king":{"name":"King","melee":1.00,"sword":1.00,"magic":1.00,"rarity":"0.02%"},
}
PETS = {
 "cursed_wolf":{"name":"Cursed Wolf","attack":0.08,"defense":0.03,"rarity":"Rare"},
 "chakra_fox":{"name":"Chakra Fox","attack":0.06,"defense":0.06,"rarity":"Epic"},
 "soul_moth":{"name":"Soul Moth","attack":0.05,"defense":0.12,"rarity":"Epic"},
 "dragonling":{"name":"Dragonling","attack":0.12,"defense":0.02,"rarity":"Legendary"},
 "void_sprite":{"name":"Void Sprite","attack":0.15,"defense":0.04,"rarity":"Mythic"},
}
CHARACTER_ATTACK_TYPES = {"sukuna":"magic","gojo":"magic","yuji":"melee","naruto":"magic","sasuke":"sword","luffy":"melee","zoro":"sword","ichigo":"sword","aizen":"magic","goku":"melee","vegeta":"melee","tanjiro":"sword","asta":"sword","deku":"melee","eren":"melee","rimuru":"magic"}
SKILL_CATEGORIES = {
 "black_flash_chain":"melee","domain_amplification":"magic","chakra_surge":"magic",
 "conquerors_haki":"melee","final_getsuga":"sword","limit_breaker":"melee",
 "thunder_god_strike":"sword","bankai_final_verdict":"sword",
 "truth_seeking_burst":"magic","infinity_big_bang":"magic",
}
WEAPON_CATEGORIES = {
 "cursed_katana":"sword","sixfold_spear":"melee","dragon_fang":"melee",
 "soul_reaper":"sword","reality_edge":"sword","stormfang":"sword",
 "zanpakuto_prime":"sword","ten_tails_staff":"magic","anti_spiral_edge":"magic",
}
ATTACK_TYPES = {"melee":"Melee","sword":"Sword","magic":"Magic"}
BOSS_KEY_POOLS = {"jjk_key":["jogo","hanami","toji","jjk_sukuna","jjk_gojo","jjk_mahito"],"jojo_key":["dio","pucci","dio_vampire","diavolo","kira"],"naruto_key":["itachi","hashirama","momoshiki","isshiki","naruto_six_paths"]}
ITEM_RECIPES = {
 "jjk_key":{"name":"JJK Key","materials":{"cursed_ash":12,"soul_fragment":8,"six_eyes":1}},
 "jojo_key":{"name":"JoJo Key","materials":{"starsteel":12,"devil_fruit_shard":8,"soul_fragment":8}},
 "naruto_key":{"name":"Naruto Key","materials":{"chakra_crystal":12,"uchiha_relic":8,"dimensional_eye":2}},
 "clan_token":{"name":"Clan Reroll","materials":{"chakra_crystal":4,"cursed_ash":4,"soul_fragment":4}},
}
DEFAULT = {"xp":0,"level":1,"points":0,"character":"sukuna","weapon":None,"weapon_damage_override":None,"mastery":{},"unlocked":[],"race":"human","clan":None,"clan_rolls":1,"inventory":{},"six_eyes_unlocked":False,"infinity_unlocked":False,"sukuna_race_unlocked":False,"wins":0,"damage":0,"active_dimension":"earth","unlocked_dimensions":["earth"],"unlocked_skills":[],"equipped_skills":{"melee":[],"sword":[],"magic":[]},"damage_boosts":0,"focus_boosts":0,"symbolic_rewards":{"xp":0,"points":0,"points_spent":0,"wins":0,"damage":0,"inventory":{},"inventory_spent":{}}}

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

def mastery_tier(xp):
 xp=int(xp)
 return 3 if xp>=20000 else 2 if xp>=5000 else 1 if xp>=1000 else 0

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



class AttackCategorySelect(discord.ui.Select):
 def __init__(self, view, categories):
  self.attack_view=view
  options=[discord.SelectOption(label=ATTACK_TYPES[key],value=key,description=f"{len(skills)} equipped skill(s)") for key,skills in categories.items()]
  super().__init__(placeholder="Choose your weapon type",min_values=1,max_values=1,options=options)
 async def callback(self,interaction):
  if interaction.user.id!=self.attack_view.ctx.author.id:
   await interaction.response.send_message("This attack menu belongs to another player.",ephemeral=True); return
  category=self.values[0]
  skills=self.attack_view.cog.attack_skill_options(self.attack_view.ctx.author.id,category)
  await interaction.response.edit_message(embed=self.attack_view.cog.embed(f"{ATTACK_TYPES[category].upper()} SKILLS","Choose one equipped skill to use for this turn."),view=AttackSkillView(self.attack_view.cog,self.attack_view.ctx,category,skills))

class AttackSkillSelect(discord.ui.Select):
 def __init__(self, view, skills):
  self.attack_view=view
  options=[discord.SelectOption(label=label[:100],value=key,description=f"Use {label}"[:100]) for key,label in skills]
  super().__init__(placeholder="Choose an equipped skill",min_values=1,max_values=1,options=options)
 async def callback(self,interaction):
  if interaction.user.id!=self.attack_view.ctx.author.id:
   await interaction.response.send_message("This attack menu belongs to another player.",ephemeral=True); return
  skill=self.values[0]
  await interaction.response.edit_message(content="Skill selected. Resolving your turn...",embed=None,view=None)
  await self.attack_view.attack_command.callback(self.attack_view.cog,self.attack_view.ctx,skill)

class AttackCategoryView(discord.ui.View):
 def __init__(self,cog,ctx,categories,attack_command=None):
  super().__init__(timeout=120); self.cog=cog; self.ctx=ctx; self.attack_command=attack_command or cog.attack
  self.add_item(AttackCategorySelect(self,categories))
 async def interaction_check(self,interaction):
  if interaction.user.id!=self.ctx.author.id:
   await interaction.response.send_message("This attack menu belongs to another player.",ephemeral=True); return False
  return True

class AttackSkillView(discord.ui.View):
 def __init__(self,cog,ctx,category,skills):
  super().__init__(timeout=120); self.cog=cog; self.ctx=ctx; self.category=category
  self.add_item(AttackSkillSelect(self,skills))
 async def interaction_check(self,interaction):
  if interaction.user.id!=self.ctx.author.id:
   await interaction.response.send_message("This attack menu belongs to another player.",ephemeral=True); return False
  return True

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
  p.setdefault("clan",None)
  p.setdefault("clan_rolls",1)
  p.setdefault("mastery",{})
  p.setdefault("active_dimension","earth")
  p.setdefault("unlocked_dimensions",["earth"])
  p.setdefault("unlocked_skills",[])
  p.setdefault("equipped_skills",{"melee":[],"sword":[],"magic":[]})
  for category in ATTACK_TYPES: p["equipped_skills"].setdefault(category,[])
  p.setdefault("damage_boosts",0)
  p.setdefault("focus_boosts",0)
  p.setdefault("symbolic_rewards",{"xp":0,"points":0,"points_spent":0,"wins":0,"damage":0,"inventory":{},"inventory_spent":{}})
  sr=p["symbolic_rewards"]
  for key,value in {"xp":0,"points":0,"points_spent":0,"wins":0,"damage":0,"inventory":{},"inventory_spent":{}}.items(): sr.setdefault(key,value)
  return p
 def attack_skill_options(self,uid,category=None):
  p=self.p(uid); custom=self.data.get("custom_weapons",{}).get(p.get("weapon"))
  c=CHARACTERS[p["character"]]; result={}
  for kind in ATTACK_TYPES:
   if category and kind!=category: continue
   options=[]
   for key in p.get("equipped_skills",{}).get(kind,[]):
    if key in SKILL_TREE and key in p.get("unlocked_skills",[]) and SKILL_CATEGORIES.get(key)==kind:
     options.append((key,SKILL_TREE[key]["name"]))
    elif key==c[5] and CHARACTER_ATTACK_TYPES.get(p["character"])==kind and (key in p.get("unlocked",[]) or (p["race"]=="vessel" and p["character"]=="sukuna")):
     options.append((key,c[4]))
   if custom and (custom.get("category") or WEAPON_CATEGORIES.get(p.get("weapon"),"melee"))==kind:
    options.append((custom["ability_key"],custom["ability"]))
   if options: result[kind]=options
  return result
 def flush(self): save(self.data)
 def embed(self,title,desc="",color=None):
  e=discord.Embed(title=title,description=desc,color=color or discord.Color.from_rgb(35,45,64)); return e
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
 @commands.command(name="clans")
 async def clans(self,ctx):
  p=self.p(ctx.author.id); current=CLANS.get(p.get("clan"))
  e=self.embed("CLAN ARCHIVE",f"Current clan: {current['name'] if current else 'Unassigned'}\nRerolls available: {p.get('clan_rolls',0)}\nUse ,clan roll to roll a new clan.")
  for key,d in CLANS.items():
   e.add_field(name=f"{d['name']} / {key}",value=f"Melee +{int(d['melee']*100)}% · Sword +{int(d['sword']*100)}% · Magic +{int(d['magic']*100)}%\nListed rarity: {d['rarity']}",inline=False)
  await ctx.reply(embed=e,mention_author=False)

 @commands.group(name="clan",invoke_without_command=True)
 async def clan(self,ctx):
  p=self.p(ctx.author.id); d=CLANS.get(p.get("clan"))
  await ctx.reply(embed=self.embed("CLAN STATUS",f"Current clan: {d['name'] if d else 'Unassigned'}\nRerolls: {p.get('clan_rolls',0)}\nUse ,clans to view bonuses or ,clan roll to reroll."),mention_author=False)

 @clan.command(name="roll")
 async def clan_roll(self,ctx):
  p=self.p(ctx.author.id)
  if p.get("clan_rolls",0)<1:
   await ctx.reply(embed=self.embed("NO CLAN REROLLS","Earn one clan reroll every 5 boss victories, or craft one with ,craft item clan_token."),mention_author=False); return
  choices=[(None,95.28),("otogakure",3.0),("satoru",0.5),("zenin",0.5),("kamo",0.5),("akatsuki",0.1),("konoha",0.1),("king",0.02)]
  result=random.choices([x[0] for x in choices],weights=[x[1] for x in choices],k=1)[0]
  p["clan_rolls"]-=1; p["clan"]=result; self.flush()
  if result is None:
   await ctx.reply(embed=self.embed("CLAN ROLL",f"You rolled no clan this time. Rerolls remaining: {p['clan_rolls']}"),mention_author=False); return
  d=CLANS[result]
  await ctx.reply(embed=self.embed("CLAN AWAKENED",f"You rolled **{d['name']}**.\nMelee +{int(d['melee']*100)}% · Sword +{int(d['sword']*100)}% · Magic +{int(d['magic']*100)}%\nRerolls remaining: {p['clan_rolls']}"),mention_author=False)

 @clan.command(name="set",aliases=["choose","select"])
 @commands.is_owner()
 async def clan_set(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_")
  if key in {"none","off","clear"}:
   p=self.p(ctx.author.id); p["clan"]=None; self.flush()
   await ctx.reply(embed=self.embed("CLAN CLEARED","Your clan has been set to Unassigned."),mention_author=False); return
  if key not in CLANS:
   names=", ".join(f"{d['name']} ({k})" for k,d in CLANS.items())
   await ctx.reply(embed=self.embed("UNKNOWN CLAN",f"Choose one of: {names}.\nUsage: ,clan set <key>"),mention_author=False); return
  p=self.p(ctx.author.id); p["clan"]=key; self.flush()
  d=CLANS[key]
  await ctx.reply(embed=self.embed("CLAN SELECTED",f"You selected **{d['name']}**.\nMelee +{int(d['melee']*100)}% · Sword +{int(d['sword']*100)}% · Magic +{int(d['magic']*100)}%"),mention_author=False)

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
 @commands.group(name="bosskey",invoke_without_command=True)
 async def bosskey(self,ctx):
  await ctx.reply(embed=self.embed("BOSS KEY VAULT","Craft keys with ,craft item <key>, then use ,bosskey use <key>.\nJJK Key · JoJo Key · Naruto Key"),mention_author=False)

 @bosskey.command(name="use")
 @commands.guild_only()
 async def bosskey_use(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_")
  key={"jjk":"jjk_key","jojo":"jojo_key","naruto":"naruto_key"}.get(key,key)
  if key not in BOSS_KEY_POOLS:
   await ctx.reply(embed=self.embed("UNKNOWN KEY","Available keys: jjk_key, jojo_key, naruto_key."),mention_author=False); return
  p=self.p(ctx.author.id)
  if not self.has_item(p,key,1):
   await ctx.reply(embed=self.embed("KEY MISSING",f"You need {ITEMS[key]}. Craft it with ,craft item {key}."),mention_author=False); return
  async with self.lock:
   g=str(ctx.guild.id)
   if g in self.data["raids"]:
    await ctx.reply(embed=self.embed("RAID ACTIVE","Finish the current raid before opening another key."),mention_author=False); return
   self.consume_item(p,key,1); boss_key=random.choice(BOSS_KEY_POOLS[key]); b=BOSSES[boss_key]
   self.data["raids"][g]={"boss":boss_key,"hp":b[1],"max_hp":b[1],"leader":str(ctx.author.id),"players":{str(ctx.author.id):250},"turns":[str(ctx.author.id)],"turn":0,"damage":{},"phase":1,"key_type":key}
   self.flush()
  await ctx.reply(embed=self.embed(f"{ITEMS[key].upper()} OPENED",f"The key summoned **{b[0]}**.\n{b[1]:,} HP · {b[2][0]}–{b[2][1]} damage · {b[3]:,} XP\nOthers can join with ,join."),mention_author=False)

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
   if ability is None:
    categories=self.attack_skill_options(ctx.author.id)
    if not categories:
     await ctx.reply(embed=self.embed("NO EQUIPPED SKILLS","Unlock skills, then equip them with ,equipskill <melee|sword|magic> <skill>. Your equipped weapon ability is available automatically."),mention_author=False); return
    await ctx.reply(embed=self.embed("CHOOSE WEAPON TYPE","Choose Melee, Sword or Magic. Then choose one equipped skill. No attack happens until you select a skill."),view=AttackCategoryView(self,ctx,categories),mention_author=False); return
   ability_key=ability.lower().strip().replace(" ","_")
   options=self.attack_skill_options(ctx.author.id)
   selected_category=next((kind for kind,items in options.items() if any(key==ability_key for key,_ in items)),None)
   if selected_category is None:
    await ctx.reply(embed=self.embed("SKILL NOT EQUIPPED","That skill is not equipped. Use ,skills and ,equipskill to set your loadout."),mention_author=False); return
   if custom and ability_key==custom["ability_key"]:
    damage=random.randint(*custom["ability_damage"]); action=custom["ability"]
    override=p.get("weapon_damage_override")
    if override=="googolplex": damage=r["hp"]
    elif override is not None: damage=int(override)
   elif ability_key==c[5]:
    if ability_key not in p["unlocked"] and not(p["race"]=="vessel" and p["character"]=="sukuna"):
     await ctx.reply(embed=self.embed("SKILL LOCKED",f"Unlock {ability_key} with ,unlock {ability_key}."),mention_author=False); return
    damage=random.randint(*c[6]); action=c[4]
   elif ability_key in p.get("unlocked_skills",[]) and ability_key in SKILL_TREE:
    sk=SKILL_TREE[ability_key]; damage=int(random.randint(*c[3])*sk["multiplier"]); action=sk["name"]
   else:
    await ctx.reply(embed=self.embed("SKILL LOCKED","That ability is not unlocked on your profile."),mention_author=False); return
   race=RACES[p["race"]]; race_mult=1.20 if p["race"]=="gojo" and p["six_eyes_unlocked"] else race[1]
   clan=CLANS.get(p.get("clan")); attack_type=selected_category
   clan_mult=1+(clan.get(attack_type,0) if clan else 0)
   level_mult=1+min(35,max(0,int(p["level"])-1))*0.01
   mastery=p.setdefault("mastery",{}); mastery_xp=int(mastery.get(p["character"],0)); mastery_level=mastery_tier(mastery_xp)
   mastery_mult=1+0.02*mastery_level
   if p.get("damage_boosts",0)>0:
    damage=int(damage*1.5); p["damage_boosts"]-=1
   if p.get("focus_boosts",0)>0:
    damage*=2; p["focus_boosts"]-=1
   gear_attack=0
   try:
    from cogs.endgame import GEAR
    for gear_key in p.get("gear_equipped",{}).values():
     if gear_key in GEAR: gear_attack+=GEAR[gear_key]["attack"]
   except ImportError: pass
   damage+=gear_attack
   dimension_mult=DIMENSIONS.get(p.get("active_dimension"),DIMENSIONS["earth"])["bonus"]
   pet=PETS.get(p.get("pet_equipped")); pet_mult=1+(pet["attack"] if pet else 0)
   damage=min(r["hp"],max(1,int(damage*race_mult*clan_mult*level_mult*mastery_mult*dimension_mult*pet_mult))); r["hp"]-=damage
   mastery[p["character"]]=mastery_xp+damage
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
      q["xp"]+=b[3]*swarm_multiplier+r["damage"].get(player_id,0)//4; q["points"]+=swarm_multiplier; old_wins=q.get("wins",0); q["wins"]+=swarm_multiplier
      q["clan_rolls"]=q.get("clan_rolls",1)+(q["wins"]//5-old_wins//5)
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
   try:
    from cogs.endgame import GEAR
    gear_defense=sum(GEAR[k]["defense"] for k in p.get("gear_equipped",{}).values() if k in GEAR)
   except ImportError: gear_defense=0
   pet_defense=pet["defense"] if pet else 0
   reduction=min(.75,reduction+gear_defense+pet_defense)
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
 @commands.command(name="mastery")
 async def mastery(self,ctx):
  p=self.p(ctx.author.id); key=p["character"]; xp=int(p.get("mastery",{}).get(key,0)); level=mastery_tier(xp)
  thresholds=[1000,5000,20000]; next_target=thresholds[level] if level<3 else None
  progress=f"{display_number(xp)} mastery XP"
  if next_target is not None: progress+=f"\nNext tier: {display_number(next_target-xp)} XP remaining"
  else: progress+="\nMaximum mastery reached"
  e=self.embed("CHARACTER MASTERY",f"**{CHARACTERS[key][0]}**\nMastery tier: {level}/3\nDamage bonus: +{level*2}%\n{progress}")
  await ctx.reply(embed=e,mention_author=False)

 @commands.command(name="equipskill")
 async def equipskill(self,ctx,category,*,skill):
  category=category.lower().strip(); key=skill.lower().strip().replace(" ","_"); p=self.p(ctx.author.id)
  if category not in ATTACK_TYPES:
   await ctx.reply(embed=self.embed("INVALID TYPE","Choose melee, sword or magic."),mention_author=False); return
  c=CHARACTERS[p["character"]]
  valid=(key in SKILL_TREE and key in p.get("unlocked_skills",[]) and SKILL_CATEGORIES.get(key)==category) or (key==c[5] and CHARACTER_ATTACK_TYPES.get(p["character"])==category and (key in p.get("unlocked",[]) or (p["race"]=="vessel" and p["character"]=="sukuna")))
  custom=self.data.get("custom_weapons",{}).get(p.get("weapon"))
  if custom and key==custom.get("ability_key"):
   await ctx.reply(embed=self.embed("WEAPON SKILL READY","Your equipped weapon ability is automatically available in its weapon category."),mention_author=False); return
  if not valid:
   await ctx.reply(embed=self.embed("SKILL UNAVAILABLE",f"That skill is not unlocked or does not belong to {category}. Check ,skills and ,skilltree."),mention_author=False); return
  equipped=p.setdefault("equipped_skills",{"melee":[],"sword":[],"magic":[]}).setdefault(category,[])
  if key in equipped:
   await ctx.reply(embed=self.embed("ALREADY EQUIPPED","That skill is already equipped."),mention_author=False); return
  if len(equipped)>=3:
   await ctx.reply(embed=self.embed("LOADOUT FULL","Each weapon type can hold up to three equipped skills. Unequip one first."),mention_author=False); return
  equipped.append(key); self.flush()
  label=SKILL_TREE[key]["name"] if key in SKILL_TREE else c[4]
  await ctx.reply(embed=self.embed("SKILL EQUIPPED",f"{label} is equipped under {ATTACK_TYPES[category]}. Use ,attack to choose it in combat."),mention_author=False)
 @commands.command(name="unequipskill")
 async def unequipskill(self,ctx,category,*,skill):
  category=category.lower().strip(); key=skill.lower().strip().replace(" ","_"); p=self.p(ctx.author.id)
  if category not in ATTACK_TYPES or key not in p.get("equipped_skills",{}).get(category,[]):
   await ctx.reply(embed=self.embed("SKILL NOT EQUIPPED","Check ,skillloadout for your current loadout."),mention_author=False); return
  p["equipped_skills"][category].remove(key); self.flush()
  await ctx.reply(embed=self.embed("SKILL UNEQUIPPED",f"{key.replace('_',' ').title()} removed from {ATTACK_TYPES[category]}."),mention_author=False)
 @commands.command(name="skillloadout",aliases=["loadout"])
 async def skillloadout(self,ctx):
  options=self.attack_skill_options(ctx.author.id); e=self.embed("COMBAT LOADOUT","Only equipped skills appear in the attack selector.")
  for category in ATTACK_TYPES:
   items=options.get(category,[])
   e.add_field(name=ATTACK_TYPES[category],value="\n".join(f"{label} ({key})" for key,label in items) or "No equipped skills",inline=False)
  await ctx.reply(embed=e,mention_author=False)

 @commands.command(name="skills")
 async def skills(self,ctx):
  p=self.p(ctx.author.id); c=CHARACTERS[p["character"]]; unlocked=c[5] in p["unlocked"] or(p["race"]=="vessel" and p["character"]=="sukuna")
  options=self.attack_skill_options(ctx.author.id)
  lines=[f"{c[0]} · {c[4]}",f"Damage: {c[6][0]}–{c[6][1]}",f"Cost: {c[7]} points",f"Status: {'Unlocked' if unlocked else 'Locked'}"]
  for category in ATTACK_TYPES:
   items=options.get(category,[])
   lines.append(f"{ATTACK_TYPES[category]}: "+(", ".join(label for _,label in items) if items else "No equipped skills"))
  lines.append("Equip: ,equipskill <type> <skill> · View: ,skillloadout")
  await ctx.reply(embed=self.embed("TECHNIQUE RECORD","\n".join(lines)),mention_author=False)
 @commands.command(name="unlock")
 async def unlock(self,ctx,*,skill):
  p=self.p(ctx.author.id); c=CHARACTERS[p["character"]]; key=skill.lower().strip().replace(" ","_")
  if key in SKILL_TREE:
   d=SKILL_TREE[key]
   missing=[f"{ITEMS.get(i,i)} x{n-int(p['inventory'].get(i,0))}" for i,n in d["materials"].items() if int(p["inventory"].get(i,0))<n]
   if key in p["unlocked_skills"]:
    await ctx.reply(embed=self.embed("ALREADY UNLOCKED",f"{d['name']} is already available."),mention_author=False); return
   if p["level"]<d["level"] or p["points"]<d["cost"] or missing:
    await ctx.reply(embed=self.embed("SKILL REQUIREMENTS",f"Level {d['level']} · {d['cost']} points\nMissing: {', '.join(missing) if missing else 'None'}"),mention_author=False); return
   for i,n in d["materials"].items(): self.item(p,i,-n)
   p["points"]-=d["cost"]; p["unlocked_skills"].append(key); self.flush()
   await ctx.reply(embed=self.embed("SKILL UNLOCKED",f"{d['name']} is ready. Damage multiplier x{d['multiplier']:.2f}."),mention_author=False); return
  if key!=c[5]: await ctx.reply(embed=self.embed("UNKNOWN SKILL",f"Your character uses {c[5]}. Use ,skilltree for more skills."),mention_author=False); return
  if key in p["unlocked"] or(p["race"]=="vessel" and p["character"]=="sukuna"): await ctx.reply(embed=self.embed("ALREADY UNLOCKED","This skill is already available."),mention_author=False); return
  if p["points"]<c[7]:
   sr=p["symbolic_rewards"]
   if sr["points"]<=sr["points_spent"]: await ctx.reply(embed=self.embed("NOT ENOUGH POINTS",f"You need {c[7]} points."),mention_author=False); return
   sr["points_spent"]+=c[7]-p["points"]; p["points"]=0
  else: p["points"]-=c[7]
  p["unlocked"].append(key); self.flush()
  await ctx.reply(embed=self.embed("SKILL UNLOCKED",c[4]+" is now available."),mention_author=False)

 @commands.command(name="skilltree")
 async def skilltree(self,ctx):
  p=self.p(ctx.author.id); e=self.embed("UNIVERSAL SKILL TREE","Unlock with ,unlock <key>. Skills need levels, points and materials.")
  for key,d in SKILL_TREE.items():
   mats=", ".join(f"{ITEMS.get(i,i)} x{n}" for i,n in d["materials"].items())
   state="UNLOCKED" if key in p["unlocked_skills"] else f"Level {d['level']} · {d['cost']} points"
   e.add_field(name=f"{d['name']} / {key} · {state}",value=f"Damage x{d['multiplier']:.2f}\nMaterials: {mats}",inline=False)
  await ctx.reply(embed=e,mention_author=False)

 @commands.command(name="recipes")
 async def recipes(self,ctx):
  e=self.embed("FORGE BLUEPRINTS","Craft a weapon with ,craft <key>.")
  for key,d in WEAPON_RECIPES.items():
   mats=", ".join(f"{ITEMS.get(i,i)} x{n}" for i,n in d["materials"].items())
   e.add_field(name=f"{d['name']} / {key}",value=f"Level {d['level']} · Damage {d['damage'][0]}–{d['damage'][1]}\n{d['ability']} · {d['ability_damage'][0]}–{d['ability_damage'][1]}\nMaterials: {mats}",inline=False)
  await ctx.reply(embed=e,mention_author=False)

 @commands.command(name="craft")
 async def craft(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_")
  if key.startswith("item_"): key=key[5:]
  if key.startswith("i_"): key=key[2:]
  if key in ITEM_RECIPES:
   p=self.p(ctx.author.id); recipe=ITEM_RECIPES[key]
   missing=[f"{ITEMS.get(i,i)} x{n-int(p['inventory'].get(i,0))}" for i,n in recipe["materials"].items() if int(p["inventory"].get(i,0))<n]
   if missing:
    await ctx.reply(embed=self.embed("CRAFTING MATERIALS MISSING",", ".join(missing)),mention_author=False); return
   for item_key,amount in recipe["materials"].items(): self.item(p,item_key,-amount)
   if key=="clan_token":
    p["clan_rolls"]=p.get("clan_rolls",1)+1; result=f"Added one clan reroll. You now have {p['clan_rolls']}."
   else:
    self.item(p,key,1); result=f"Created {recipe['name']} x1."
   self.flush()
   await ctx.reply(embed=self.embed("ITEM CRAFTED",result),mention_author=False); return
  p=self.p(ctx.author.id); d=WEAPON_RECIPES.get(key)
  if not d:
   await ctx.reply(embed=self.embed("BLUEPRINT NOT FOUND","Use ,recipes or ,craft item <key>."),mention_author=False); return
  owned=self.data.setdefault("crafted_weapons",{}).setdefault(str(ctx.author.id),[])
  if key in owned:
   await ctx.reply(embed=self.embed("ALREADY FORGED","You already crafted this weapon."),mention_author=False); return
  missing=[f"{ITEMS.get(i,i)} x{n-int(p['inventory'].get(i,0))}" for i,n in d["materials"].items() if int(p["inventory"].get(i,0))<n]
  if p["level"]<d["level"] or missing:
   await ctx.reply(embed=self.embed("FORGE REQUIREMENTS",f"Required level: {d['level']}\nMissing materials: {', '.join(missing) if missing else 'None'}"),mention_author=False); return
  for i,n in d["materials"].items(): self.item(p,i,-n)
  self.data["custom_weapons"][key]={k:d[k] for k in ("name","damage","ability","ability_key","ability_damage","description")}
  owned.append(key); p["weapon"]=key; self.flush()
  await ctx.reply(embed=self.embed("WEAPON FORGED",f"{d['name']} crafted and equipped. Use ,attack {d['ability_key']}."),mention_author=False)

 @commands.group(name="dimension",invoke_without_command=True)
 async def dimension(self,ctx):
  await ctx.invoke(self.dimension_list)

 @dimension.command(name="list")
 async def dimension_list(self,ctx):
  p=self.p(ctx.author.id); e=self.embed("DIMENSION GATEWAY",f"Current world: {DIMENSIONS.get(p['active_dimension'],DIMENSIONS['earth'])['name']}")
  for key,d in DIMENSIONS.items():
   state="UNLOCKED" if key in p["unlocked_dimensions"] else f"Level {d['level']} · {d['wins']} victories"
   mats=", ".join(f"{ITEMS.get(i,i)} x{n}" for i,n in d["materials"].items()) or "None"
   e.add_field(name=f"{d['name']} / {key} · {state}",value=f"{d['description']}\nEntry materials: {mats}\nDamage affinity: +{int((d['bonus']-1)*100)}%",inline=False)
  await ctx.reply(embed=e,mention_author=False)

 @dimension.command(name="enter")
 async def dimension_enter(self,ctx,*,key):
  key=key.lower().strip().replace(" ","_"); p=self.p(ctx.author.id); d=DIMENSIONS.get(key)
  if not d:
   await ctx.reply(embed=self.embed("UNKNOWN DIMENSION","Use ,dimension list."),mention_author=False); return
  if key not in p["unlocked_dimensions"]:
   missing=[f"{ITEMS.get(i,i)} x{n-int(p['inventory'].get(i,0))}" for i,n in d["materials"].items() if int(p["inventory"].get(i,0))<n]
   if p["level"]<d["level"] or p["wins"]<d["wins"] or missing:
    await ctx.reply(embed=self.embed("GATE SEALED",f"Level {d['level']} · {d['wins']} victories\nMissing: {', '.join(missing) if missing else 'None'}"),mention_author=False); return
   for i,n in d["materials"].items(): self.item(p,i,-n)
   p["unlocked_dimensions"].append(key)
  p["active_dimension"]=key; self.flush()
  await ctx.reply(embed=self.embed("DIMENSION ENTERED",f"You entered {d['name']}. Damage affinity: +{int((d['bonus']-1)*100)}%."),mention_author=False)

 @commands.command(name="inventory",aliases=["inv","bag"])
 async def inventory(self,ctx,page:int=1):
  from cogs.render_ui import inventory_image
  p=self.p(ctx.author.id); sr=p["symbolic_rewards"]
  entries=sum(1 for v in p["inventory"].values() if v>0)+sum(1 for v in sr["inventory"].values() if v>0)
  pages=max(1,(entries+14)//15); page=max(1,min(page,pages))
  image=inventory_image(p,ITEMS,page)
  file=discord.File(image,filename="inventory.png")
  e=self.embed("INVENTORY",f"{entries} item stacks · page {page}/{pages}\nUse ,inventory <page> to browse.")
  six=p["inventory"].get("six_eyes",0); fingers=p["inventory"].get("cursed_fingers",0)
  six_label=symbolic_quantity(sr["inventory"]["six_eyes"],sr["inventory_spent"].get("six_eyes",0)) if sr["inventory"].get("six_eyes",0) else display_number(six)
  finger_label=symbolic_quantity(sr["inventory"]["cursed_fingers"],sr["inventory_spent"].get("cursed_fingers",0)) if sr["inventory"].get("cursed_fingers",0) else display_number(fingers)
  e.add_field(name="Awakening progress",value=f"Six Eyes: {six_label}/6\nCursed Fingers: {finger_label}/20\nRace: {RACES[p['race']][0]}",inline=False)
  e.set_image(url="attachment://inventory.png")
  await ctx.reply(embed=e,file=file,mention_author=False)
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
  key=item.lower().strip().replace(" ","_"); p=self.p(ctx.author.id)
  g=str(ctx.guild.id) if ctx.guild else ""
  async with self.lock:
   r=self.data["raids"].get(g)
   uid=str(ctx.author.id)
   if key in {"phoenix_feather","phoenix"}:
    if not r or uid not in r["players"] or r["players"][uid]>0:
     await ctx.reply(embed=self.embed("CANNOT USE","You must be a defeated party member in an active raid."),mention_author=False); return
    if not self.has_item(p,"phoenix_feather",1):
     await ctx.reply(embed=self.embed("ITEM MISSING","You need a Phoenix Feather."),mention_author=False); return
    self.consume_item(p,"phoenix_feather",1); r["players"][uid]=150; self.flush()
    await ctx.reply(embed=self.embed("PHOENIX REVIVAL","You returned to the raid with 150 HP."),mention_author=False); return
   if key=="healing_potion":
    if not r or uid not in r["players"] or r["players"][uid]<=0:
     await ctx.reply(embed=self.embed("CANNOT USE","Healing Potions can only be used by a living raid member."),mention_author=False); return
    if r["players"][uid]>=250:
     await ctx.reply(embed=self.embed("HEALTH FULL","You already have full HP."),mention_author=False); return
    if not self.has_item(p,key,1):
     await ctx.reply(embed=self.embed("ITEM MISSING","You do not have a Healing Potion."),mention_author=False); return
    self.consume_item(p,key,1); r["players"][uid]=min(250,r["players"][uid]+100); hp=r["players"][uid]; self.flush()
    await ctx.reply(embed=self.embed("POTION USED",f"Restored up to 100 HP. Current HP: {hp}/250."),mention_author=False); return
   if key in {"battle_tonic","focus_elixir"}:
    if not r or uid not in r["players"] or r["players"][uid]<=0:
     await ctx.reply(embed=self.embed("CANNOT USE","Combat tonics can only be prepared during an active raid while alive."),mention_author=False); return
    if not self.has_item(p,key,1):
     await ctx.reply(embed=self.embed("ITEM MISSING",f"You do not have {ITEMS[key]}."),mention_author=False); return
    self.consume_item(p,key,1)
    if key=="battle_tonic": p["damage_boosts"]+=1; effect="Your next attack deals 50% bonus damage."
    else: p["focus_boosts"]+=1; effect="Your next attack deals double damage."
    self.flush()
    await ctx.reply(embed=self.embed(f"{ITEMS[key].upper()} ACTIVE",effect),mention_author=False); return
   if key=="awakening_crystal":
    if not self.has_item(p,key,1):
     await ctx.reply(embed=self.embed("ITEM MISSING","You do not have an Awakening Crystal."),mention_author=False); return
    self.consume_item(p,key,1); p["points"]+=5; self.flush()
    await ctx.reply(embed=self.embed("CRYSTAL CONSUMED","You gained 5 skill points."),mention_author=False); return
  await ctx.reply(embed=self.embed("ITEM NOT USABLE","Try Healing Potion, Battle Tonic, Focus Elixir, Awakening Crystal or Phoenix Feather."),mention_author=False)

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
  mastery_level=mastery_tier(p.get("mastery",{}).get(p["character"],0))
  clan_name=CLANS.get(p.get("clan"),{}).get("name","Unassigned")
  desc=(f"Title: {title_name}\nCharacter: {c[0]}\nClan: {clan_name}\nMastery: Tier {mastery_level}/3 (+{mastery_level*2}% damage)\nRace: {RACES[p['race']][0]}\nLevel: {display_number(p['level'])}\nXP: {display_number(p['xp'])} / {display_number(p['level']*250)}\nSkill points: {display_number(p['points'])}\nVictories: {display_number(p['wins'])}\nTotal damage: {display_number(p['damage'])}" + ("\n" + "\n".join(symbolic_lines) if symbolic_lines else ""))
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
  if key in WEAPON_RECIPES and key not in self.data.get("crafted_weapons",{}).get(str(ctx.author.id),[]):
   await ctx.reply(embed=self.embed("WEAPON LOCKED","Craft this weapon yourself with ,craft "+key+"."),mention_author=False); return
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
  p=self.p(member.id)
  if key=="clan_token":
   p["clan_rolls"]=p.get("clan_rolls",1)+amount; result=f"Granted {amount} clan rerolls to {member.mention}. Total: {p['clan_rolls']}."
  else:
   self.item(p,key,amount); result=f"Granted {ITEMS[key]} x{amount} to {member.mention}."
  self.flush()
  await ctx.reply(embed=self.embed("OWNER GRANT",result),mention_author=False)
 @commands.command(name="addclanrolls",aliases=["clanrolls"])
 @commands.is_owner()
 async def addclanrolls(self,ctx,member:discord.User,amount:int):
  if not 1<=amount<=1000000:
   await ctx.reply(embed=self.embed("INVALID AMOUNT","Choose an amount from 1 to 1000000."),mention_author=False); return
  p=self.p(member.id); p["clan_rolls"]=p.get("clan_rolls",1)+amount; self.flush()
  await ctx.reply(embed=self.embed("CLAN REROLLS GRANTED",f"Added {amount:,} rerolls to {member.mention}. Total: {p['clan_rolls']:,}."),mention_author=False)

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
