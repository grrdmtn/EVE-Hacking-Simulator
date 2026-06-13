## EVE Hacking Simulator

![EVE Hacking Simulator](https://github.com/grrdmtn/EVE-Hacking-Simulator/blob/d760df856e8a855508b58465d6a66d1613f04763/EVE%20Hacking%20Simulator%20screenshot.png)

## What am I looking at?

This is a fully functional offline version of the original hacking minigame within Fenris Creation's EVE Online. 

With this sim you can pick your own values for player and board stats, which for example allows you to see if an expensive *Zeugma Integrated Analyzer* with *Neural Lace 'Blackglass' Net Intrusion 920-40* is worth the upgrade before you buy it, or allows you to play your favourite minigame on a much larger board or with stronger and more defences if you wanted, or feel unbeatable as you kill everything with your modified 100 strength 

... sadly you don't get any of the sweet valuable explorer loot for completing hacks in this simulation. :( 

I hope you have as much fun with this as I had building it!


## How to run

1. Copy the **'EVE_hacking_simulator.py'** file and **'images'** folder both to a single location of your choice
2. *(Probably take a glance at the Python code, I wouldn't blindly run something from the internet)*
3. Run the file with Python

For example navigate to the location you picked in File Explorer, type 'cmd' and then Enter in the bar to open command prompt at that location. Then run `python EVE_hacking_simulator.py` to start.

Alternatively and maybe easier:

Copy the path to the file including the filename. Create a new desktop shortcut using that path. **Done!**

I've added three icon images to the image folder for the shortcut so you can pick your favourite analyzer tool.

## Questions, bugs, feedback or other remarks?

Contact Gerard Amatin:

I occasionally read my EVE mail, or else you can post in [the forum thread here](https://forums.eveonline.com/t/eve-hacking-simulator/513203).

## Future plans

Now that the base game is fully functional I'm sharing it, but I still plan to do the following:
- ~~add support to change game difficulty~~ - Done!
- verify (and if wrong: fix) all the assumptions I made for some of the more niche interactions within the game
- add better visual feedback to using the utility tool buttons
- add a menu for easy changing of settings (so that you don't need to change those in the file)
- add support for custom defenses and utilities
- make a bunch of custom defenses and utilities

## Custom defenses and utilities?

Yes! It was one of the reasons I wanted to make this sim, to test some ideas I had. As someone who loves the activity of exploration in EVE Online, scanning and hacking data sites, relic sites, ghost sites and sleeper sites and has fun with this minigame I've often wondered why relic and data sites are exactly the same.

Why don't they have some unique differences so that hacking a data site *feels* different than a relic site?

Also, this minigame may put too much emphasis on strength in it's current state. Defense nodes hit last and cannot hit back if they are dead, which means increasing strength ironically often is better for your coherence than increasing coherence. This makes a *Neural Lace 'Bluefire' Net Ablation 960-10* implant (which sacrifices strength to add coherence) a questionable choice.

Lastly I think the minigame could do with some more strategic choices. Often the best thing to do is 'just blindly kill any defense nodes that pop up', especially when you're at 60 strength. Wouldn't it be nice if there was a valid choice to leave certain defense nodes alive longer?

Maybe I (and others using this tool) can come up with creative ideas that address those issues, and hopefully the feedback can even get Fenris Creations to further improve their hacking minigame!

Or if not, at least we can have fun with it.
