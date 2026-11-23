# Lifelike Motion (Forge 1.20.1)

Everything you do gets an animation.

- **Weighty first person** – your arm holds the item; sword slashes alternate forehand / backhand, axes chop overhead,
  pickaxes strike, shovels scoop, empty hands jab. The hands lag when you turn, bob and pump when you walk and sprint,
  trail your jumps and dip when you land; lanterns and torches swing.
- **Every item has its own stance** – how it's held standing, walking and running: tools go over the shoulder when you
  run, a sword is held up and ready, a torch or lantern is held out to light the way, fists pump. Stand still for a
  moment and you show off what you hold: sword twirls and blade wipes, axe and tool tosses, spins, juggling a snowball,
  turning food over to look at it, raising a lantern, cracking your knuckles. Some items have a move of their own: checking a compass, reading a book, sloshing a
  bucket, striking flint and steel (with sparks), peeking through a spyglass, holding up a totem, tossing an egg.
  Press **I** to do it any time.
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

