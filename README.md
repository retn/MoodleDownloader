# MoodleDownloader
A small - hacked - script for automatically downloading latest file from moodle courses

## How to use
1. Change the URL in moodleDownloader.py
2. Create a config file - see config file down below
3. Create a caller script for the class - if you want to use it directly
4. Start the script
5. Have fun

## caller script
```bash
#!/usr/bin/python
from moodleDownloader import MoodleDownloader

md = MoodleDownloader('$USERNAME', '$PASSWORD', 'https://url.of.the.moodle.instance/')

md.start()
```

## config file
The name of the config file is 'config', it contains a JSON object:
```JSON
{
	"Name" : {
		"ID" : "42",
		"type" : {
      "Lecture" : "/path/to/storage"
    }
	}
}
```

- **Name**
	The name is only used in the log
- **ID**
	value of the id parameter from the course URL
- **Lecture**
	is the name of the category

Multiple type's are allowed in one config file.
