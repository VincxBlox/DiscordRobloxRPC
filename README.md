# DiscordRobloxRPC
 Communicates with Discord that makes a RPC for Roblox.
 
 This basically looks every 5seconds to see if Roblox is running (I'm sure there is a better way to do this but I'm too lazy)
 If RobloxBetaPlayer.exe is running, it will go look at the logs of the Roblox user installation logs. If Roblox has been installed globally,
 it will look for the global Roblox logs. It will then look for the place id, lookup the place ID to see the name of the game, then puts it 
 in the Discord RPC, it includes a timer, and logging to a file in local folder. I recommend putting it in your USER startup folder.
 Since you need cfg.json and dcrblx.log in the working folder, they may appear as a startup element in task manager. Just disable them, I don't think there is
 any real harm to this.
 
 This is a very basic script but useful
 
 
 
 
 SET IT UP:
	1: Go in Discord and set Roblox to not be recognized.
	2: Go to [Discord Dev Portal](https://discord.com/developers/applications) and make an application named "Roblox" (you can name it what you want but this will be what shows up on your profile)
	3: Copy Application ID and paste it in cfg.json
	4: Download source code and use either the python version (for debugging and whatnot?) or the .exe versions (there is one that runs in background and one shows a console)
	5: Test it. If the game shows up on your profile, you should be good to go.
	6: Set your images, interval, application ID in cfg.json.
	
	
	
 WHAT DOES THIS do
 
 It allows to show the game you are playing instead of just saying "Playing Roblox".
 
![alt text](https://cdn.discordapp.com/attachments/1274361789324328992/1289783763202605219/image.png?ex=66fc0e7c&is=66fabcfc&hm=b13d40334bcf87d1dfefb239c51b3327c150877468774865be6318c6bdb2c979& "Updated")
![alt text](https://cdn.discordapp.com/attachments/1274361789324328992/1289785839550992534/image.png?ex=66fc106b&is=66fabeeb&hm=705db7c5e632e956939831900477381f9781b4d913fa2cc4ff971cc5ae28e374& "Generic")

