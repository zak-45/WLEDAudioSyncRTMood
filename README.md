## WLEDAudioSyncRTMood

Real Time Music mood detection. Generating colors based on. Send data to OSC server.

This python script records sound and - when music is detected - it estimates the underlying mood (emotion). Based on that it generates a respective color. If available, it can even set your Yeelight Bulb color (again based on the detected musical mood). 

See this repo : https://github.com/tyiannak/color_your_music_mood for more informations.

Additional to that, some features has been added and the main one is to send datas & color to OSC server.

Just enter :
```
python main.py -h
```
to see all options.

### Infos:

Trained models scikit-learn==0.23.2

A 5 seconds delay is present, necessary time to capture and estimate mood.

Confirmed to work with python 3.8.9, other versions need deep analysis.
