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
```
usage: main.py [-h] [-d DEVICES [DEVICES ...]] [-cs [2-20]] [-bs {0.25,0.5,0.75,1}] [-fs {4000,8000,16000,32000,44100}] [-sc {Y,N}] [-srv SERVER]
               [-p [1-65536]] [-s {Y,N}] [-v {Y,N}]

Real time audio mood analysis sent via OSC

optional arguments:
  -h, --help            show this help message and exit
  -d DEVICES [DEVICES ...], --devices DEVICES [DEVICES ...]
                        IPs to Yeelight device(s) to use
  -cs [2-20], --capture [2-20]
                        Number of second to capture, default to 5
  -bs {0.25,0.5,0.75,1}, --blocksize {0.25,0.5,0.75,1}
                        Recording block size, default to 1
  -fs {4000,8000,16000,32000,44100}, --samplingrate {4000,8000,16000,32000,44100}
                        Sample rate, default to 8KHz
  -sc {Y,N}, --screen {Y,N}
                        display color window, default to N
  -srv SERVER, --server SERVER
                        IP of the OSC server, default to 127.0.0.1
  -p [1-65536], --port [1-65536]
                        port number, default to 12000
  -s {Y,N}, --send {Y,N}
                        send to OSC, default to Y
  -v {Y,N}, --verbose {Y,N}
                        display verbose informations, default to N
```



### Python modules 

This is the name and version of python modules present on the Windows portable version
```
colorama            0.4.6
contourpy           1.1.1
coverage            5.5
cycler              0.12.1
deprecation         2.1.0
enum-compat         0.0.3
** eyed3               0.9.7 
filetype            1.2.0
fonttools           4.43.1
future              0.18.3
importlib-resources 6.1.0
joblib              1.3.2
kiwisolver          1.4.5
** matplotlib          3.5.0
msvc-runtime        14.28.29910
** numpy               1.19.0
** opencv-python       4.2.0.34
packaging           23.2
Pillow              10.1.0
pip                 23.3
** plotly              5.17.0
** PyAudio             0.2.13
** pyAudioAnalysis     0.3.6
** pydub               0.25.1
pyparsing           3.1.1
pypiwin32           223
python-dateutil     2.8.2
** python-osc          1.8.3
pywin32             306
** scikit-learn        0.23.2
** scipy               1.5.2
setuptools          56.0.0
setuptools-scm      8.0.4
six                 1.16.0
sqlite-bro          0.9.1
tenacity            8.2.3
threadpoolctl       3.2.0
toml                0.10.2
tomli               2.0.1
** tqdm                4.66.1
typing_extensions   4.8.0
```

### Infos:

Trained models scikit-learn==0.23.2

A 5 seconds delay is present, necessary time to capture and estimate mood. This is by default but can be changed with option -cs.

Confirmed to work with python 3.8.9, other versions need deep analysis.
