# DiscordRobloxRPC
 Communicates with Discord that makes a RPC for Roblox.
 
 This basically looks every 3 seconds (changable) to see if Roblox is running (I'm sure there is a better way to do this but I'm too lazy)
 If RobloxBetaPlayer.exe is running, it will go look at the logs of the Roblox user installation logs. If Roblox has been installed globally,
 it will look for the global Roblox logs. It will then look for the place id, lookup the place ID to see the name of the game, then puts it 
 in the Discord RPC, it includes a timer, and logging to a file in local folder. I recommend putting it in your USER startup folder.
 Since you need cfg.json and dcrblx.log in the working folder, they may appear as a startup element in task manager. Just disable them, I don't think there is
 any real harm to this. if large_image in cfg.json is set to AUTO, it will fetch the game thumbnail from roblox CDN and use that.
 Also disable detection level for Roblox for ppl who use MSI afterburner. You can do it yourself, but I thought this was neat.
 You can add your own buttons in the RPC, currently this is restricted to having a link that automatically goes to your profile, and the other one goes to the game you are playing right now, but this might change in the future...
 You can leave it on AUTO which will fetch the game name and fetch your display name and just use that for the button name, you can also fully disable them by setting them to false.
 Or, put your own text.
 
 This is a very basic script but useful.
 
 
 
 
 SET IT UP:
	1: Go in Discord and set Roblox to not be recognized.
	2: Go to [Discord Dev Portal](https://discord.com/developers/applications) and make an application named "Roblox" (you can name it what you want but this will be what shows up on your profile)
	3: Copy Application ID and paste it in cfg.json
	4: Download source code and use either the python version (for debugging and whatnot?) or the .exe versions (there is one that runs in background and one shows a console)
	5: Test it. If the game shows up on your profile, you should be good to go.
	6: Set your settings cfg.json.
	
	
	
 WHAT DOES THIS do
 
 It allows to show the game you are playing instead of just saying "Playing Roblox", and can also fetch the game thumbnails and apply that in Discord or use your own image.
 Also automatically turns off detection lvl in RTSS so roblox launches for ppl with MSI Afterburner

 
![alt text](https://i.imgur.com/mGODdiB.png "Updated")
![alt text](https://i.imgur.com/xjBYIET.png "Generic")

