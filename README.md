# Lifelike Motion (Forge 1.20.1)

Everything you do gets an animation.

- **3D items** – Blockbench-style models of the actual things (a sword with a guard, gems and a wrapped grip, an axe,
  an apple with a stem and leaf, a glass bottle you can see the drink through, a bucket with a handle), each with its
  own hand-tuned pixel-art textures. A built-in resource pack, *Lifelike 3D Items*, switched on the first time you
  start the game; the inventory keeps the usual flat icons. Made by `tools/models.py` (preview:
  `tools/blender/preview_json.py`).
- **Weighty first person** – your arm always holds what you carry, and hitting and working are different moves. Hit
  something with a sword and it's a three-hit combo: a flat swipe right to left, the blade flipped round for a swipe back
  left to right (the tip always leads the way it moves), then a thrust. Other tools swing as weapons (an axe comes down
  in a heavy blow). Break a block and the tool does its own job, again and again while the block breaks (a pickaxe
  picks, an axe chops, a shovel plunges in and lifts, a hoe hoes, a sword cuts). The hands lag when you turn, bob and
  pump when you walk and sprint, trail your jumps and dip when you land; lanterns and torches swing.
- **Every item has its own stance** – how it's held standing, walking and running: tools go over the shoulder when you
  run, a sword is held up and ready, a torch or lantern is held out to light the way, fists pump.
- **Show off (Y)** – press **Y** with a sword, pickaxe, axe, shovel or hoe and your arm comes up to show it off: sword
  twirls, blade wipes and flips, tool tosses, spins and resting it on your shoulder.
- **Using things** – buckets are tipped out or dipped to scoop, flint and steel is struck (sparks), shears snip, bone
  meal and seeds are shaken out, a hoe tills (soil flies), an axe shaves a log, a shovel presses a path, a rod is cast
  and reeled in. Soup is slurped from the bowl, carrots nibbled, milk chugged. A bow held drawn too long trembles; a
  shield is knocked back when it blocks.
- **Working the world** – your hand reaches out to open chests, doors and gates, pokes buttons and pulls levers. Both
  hands swim, climb ladders hand over hand, hold the reins or row a boat. You stretch when you wake up, toss what you
  drop, flinch when hit and pat at yourself when on fire.
- **Physics** – held things have weight: they lag and swing on when you start and stop, float up off your palm when you
  fall and land back with a thump (heavier things harder), lanterns swing like pendulums, cloth (beds, banners, wool)
  flutters, liquids slosh, and under water everything moves slow.
- **Lively bodies** – breathing, a torso that twists and bounces with each step, leaning into a sprint, knees up on a
  jump and flailing on a fall, a squash on landing, paddling and kicking in water, a flutter kick when swimming, hand over
  hand up ladders, flinching when hurt, food to the mouth, big readable swings.
- **Livelier mobs** – farm animals breathe, bob and glance around, chickens pump their heads, tamed wolves wag, creepers
  sway, spiders twitch, villagers nod, zombies shamble and skeletons rattle.
- **Emotes** – hold **B** for the wheel: wave, clap, cheer, point, bow, facepalm, dance, sit (keys 1-8 pick directly).
  You see them in first and third person; on a server that also has the mod, other players with it see them too.

Client-side: servers don't need it (installing it on a server only adds emote sharing). Settings: *Mods → Lifelike Motion → Config*.

## Building

`./gradlew build` (Java 17). Every push runs GitHub Actions: build, a server start-up check, then the game on a virtual
display that goes through every animation and saves a screenshot of each to the `ci-logs` branch.

