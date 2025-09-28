# JellySync
Foreked from https://github.com/Marc-Vieg/Emby2Jelly and all credit to Marc-Vieg.
This version is Jellyfin ONLY and renamed to JellySync. 
Its has been modified to include wacthed progress and works with modern Jellyfin versions (i.e. 10.10.7)

Python script to recreate users from one Jellyfin insance to another and migrate their watched content for movies and TV shows.

Can also be used to create or read from a backup file of watched status of every library item in a JSON file.

The script works by comparing the source and destination episodes and movies based on their their ProviderIds (theTvdb, Imdb...)
If ProviderIds are not available, it will try to recognize your media by names (`Les Animaux fantastiques : Les Crimes de Grindelwald`) 

***New and old instance MUST be running, pointed at the same set of media and be fully up to date and preferably with the same providers for metadata. 

---
### Requirements
python3
```
json
requests
urllib.parse
configobj
time
getpass
argparse
```
## Configuration
Simply create or edit jellysync.ini with your Jellyfin Source and Destination urls and api keys
For users that you do NOT want to copy, add htem to the IGNORE USERS section
```
[Source]
SOURCE_APIKEY = 'aaaaaaaabbbbbbbcccccddddddddwww'
SOURCE_URLBASE = 'http://192.168.1.100:8096/'
IGNORE_USERS = 'User2,admin'
[Destination]
DEST_APIKEY = 'ccccbbbbeeejjjjssssuuuaaaaiidkkdd'
DEST_URLBASE = 'http://192.168.1.100:8099/'

# Do not forget the trailing slash 

## If you have a custom path, or a reverse proxy, do not forget /jellyfin/ 
```

---

## Using
```
python3 jellysync.py 
Option Argument : (only one file can be used at a time, one run to a file, then one run from a file)
If setting up new usrs on the Destination, you may set a default with new-user-password
			--tofile [file]     	run the script saving viewed statuses to a file instead of sending them to destination server
			--fromfile [file]       run the script with a file as source server and send viewed statuses to destination server
			--pw [password]			define a password for newly created users
```

### Users
the script will get user list from Source:

```
[user@computer JellySync]$ python3 jellysync.py
no file specified, will run from source server to destination server
Source has 5 Users
George (1 / 5) : 95fththh2440a9138013619732e46
Linda (2 / 5) : c40c4b3ff833453c881efe20544f8a3
Mary (3 / 5) : e4efeefefef450cb12b017de01ba9c3
John (4 / 5) : de02ac2a8ththhhfb72284e1f6a565

```

### Source Process
then very rapidly, it will get the viewed contend for all users from the Source

`##### SourceSync Done #####
`

### Destination Process
The script will work user by user and create them on the Destination if they don't already exist.
Then it will query the destination for their viewable content 

**When creating users, the script will use --pw if specified OR ask you for password and confirmation.**
```
TestUser ..  Creating
you will now enter password for user TestUser
Password : 
confirm   : 
TestUser  Created
```
**For existing users (i.e. already created on the destination) you must specify the password already set
Passwords MAY be blank, but you will get a warning.
Password MUST match what is IN the destination for an exiting user. 

```
Destination has 5 Users
Destination already knows John (Id acebf5b7fd4cghbvcfg97b5f3a898d4)

Enter password for user John
Password :
confirm   : 
Warning ! Password is set to empty !


```


For each library item on the Source, the script will look for a matching title on Destination.
If a match is found, the full UserItems/UserData section will be updated to match the source. 



```
found by name 101 - Towne Hall Follies
found by name 102 - The Quail Hunt

```
Working by Id the major part
```
OK ! 1/17 - 101 - Towne Hall Follies has been seen by TestUser

OK ! 2/17 - Night Mission: Stealing Friends Back has been seen by TestUser

OK ! 3/17 - 102 - The Quail Hunt has been seen by TestUser

...

```
## Result

The script will generate a RESULTS.txt with summary for each user and a list of the media not found : 
```
                      ### JellySync ###


TestUser Created on Jelly


--- TestUser ---
Medias Migrated : 17 / 18
Unfortunately, I Missed 1 Medias :
[{'Type': 'Episode', 'EmbyId': '97723', 'JellyId': None, 'Name': 'La Griffe du passé', 'ProviderIds': {'Tvdb': '6218102', 'Imdb': 'tt5989942'}}]
```

### Timing
just start the script, sip a beer and it'll get done
example with a decent user (2986 media seen)

```
$time python3 jellysync.py
real	5m22,223s
user	0m43,433s
sys	0m1,485s
```


