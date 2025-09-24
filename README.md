# JellySync

Python script to recreate users from one Jellyfin insance to another and migrate their watched content for movies and TV shows.

The script works by comparing the source and destination episodes and movoes based on their their ProviderIds (theTvdb, Imdb...)
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
```
## Configuration
simply edit settings.ini with your emby and jelly url and api keys
```
[Emby]
EMBY_APIKEY = aaaabbbbbbbcccccccccccccdddddddd
EMBY_URLBASE = http://127.0.0.1:8096/
[Jelly]
JELLY_APIKEY = eeeeeeeeeeeeeeeffffffffffffffffggggggggg
JELLY_URLBASE = http://127.0.0.1:8096/ 

# do not forget the trailing slash 

## if you have a custom path, or a reverse proxy, do not forget /emby/ or /jelly/ 
```

---

## Using
```
python3 APImain.py 
Migrate from Emby to Jellyfin (or Jellyfin to Jellyfin)
Option Argument : (only one file can be used at a time, one run to a file, then one run from a file)
			--tofile [file]     run the script saving viewed statuses to a file instead of sending them to destination server
			--fromfile [file]       run the script with a file as source server and send viewed statuses to destination server
			--new-user-pw "change-your-password-9efde123"
```

### users
the script will get user list from Emby,

```
[user@computer Emby2Jelly]$ python3 APImain.py 
Emby has 1 Users
TestUser (1 / 1) : aaaabbbbbcccc4555577779999444422

```

### Emby part
then very rapidly, it will get the viewed contend for all users from emby

`##### EmbySync Done #####
`

### Jelly part
the script will work user by user (create them on Jelly if they don't already exist),
asking Jelly for their viewable content 

**When creating users, the script will ask you for password and confirmation.**
```
TestUser ..  Creating
you will now enter password for user TestUser
Password : 
confirm   : 
TestUser  Created
```



Identify your media and tell to jelly the user already seen it


working by name when there is no ProviderId


```
found by name 101 - Towne Hall Follies
found by name 102 - The Quail Hunt

```
Working by Id the major part
```
OK ! 1/17 - 101 - Towne Hall Follies has been seen by TestUser

OK ! 2/17 - Night Mission: Stealing Friends Back has been seen by TestUser

OK ! 3/17 - 102 - The Quail Hunt has been seen by TestUser

OK ! 4/17 - Zombie Island... In Space has been seen by TestUser

OK ! 5/17 - An American Story has been seen by TestUser

OK ! 6/17 - Babysitting Unibaby has been seen by TestUser

OK ! 7/17 - Birthday Month has been seen by TestUser

OK ! 8/17 - The Rabbit Who Broke All the Rules has been seen by TestUser

OK ! 9/17 - No More Bad Guys has been seen by TestUser

OK ! 10/17 - Super Axe has been seen by TestUser

OK ! 11/17 - When Night Creatures Attack has been seen by TestUser

OK ! 12/17 - 28 Days Before has been seen by TestUser

OK ! 13/17 - Taxi Cop has been seen by TestUser

OK ! 14/17 - The Dumb List has been seen by TestUser

OK ! 15/17 - 2 Guns has been seen by TestUser

OK ! 16/17 - 2001 : l'odyssée de l'espace has been seen by TestUser

OK ! 17/17 - Alabama Monroe has been seen by TestUser

```
## Result

The script will generate a RESULTS.txt with summary for each user and a list of the media not found : 
```
                      ### Emby2Jelly ###


TestUser Created on Jelly


--- TestUser ---
Medias Migrated : 17 / 18
Unfortunately, I Missed 1 Medias :
[{'Type': 'Episode', 'EmbyId': '97723', 'JellyId': None, 'Name': 'La Griffe du passé', 'ProviderIds': {'Tvdb': '6218102', 'Imdb': 'tt5989942'}}]
```

### Timing
just start the script, sip a beer and i'll be done
example with a decent user (2986 media seen)

```
$time python3 APImain.py
real	5m22,223s
user	0m43,433s
sys	0m1,485s
```


# CONTRIBUTE

Feel free to contribute however you want, I will be a pleasure !

