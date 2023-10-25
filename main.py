"""
This demo records sound and - when music is detected - it estimates the
underlying mood (emotion) and based on that it generates a respective color.
If available, it can even set your Yeelight Bulb color
(again based on the detected musical mood)

Calculated datas, include color in R G B format, will be JSON formated
and sent to OSC server.
"""
import os
import sys
import numpy
import argparse
import scipy.io.wavfile as wavfile
from pyAudioAnalysis.MidTermFeatures import mid_feature_extraction as mF
from pyAudioAnalysis import audioTrainTest as aT
import datetime
import signal
import pyaudio
import struct
from yeelight import Bulb
import cv2
import color_map_2d

from pythonosc import udp_client

global fs
global all_data
global outstr
fs = 8000
FORMAT = pyaudio.paInt16

global client
global delay
global restart

"""
necessary to be able to load file when using nuitka --nofile option 
"""
def load_file(file_name: str) -> str:
        return os.path.join(os.path.dirname(__file__), file_name)

"""
restart script to free memory
"""
def prog_restart():
    print("restarting ....")
    if "python" in sys.executable:
        print(sys.argv)
        os.execv(sys.executable, [os.path.basename(sys.executable)] + sys.argv)
    else:
        sys.argv.pop(0)
        print(sys.argv)        
        os.execv(sys.executable, sys.argv)

"""
Load 2D image of the valence-arousal representation and define coordinates
of emotions and respective colors
"""
img = cv2.cvtColor(cv2.imread(load_file("./assets/music_color_mood.png")),
                   cv2.COLOR_BGR2RGB)

"""
Color definition and emotion colormap definition
"""
colors = {
          "orange": [255, 165, 0],
          "blue": [0, 0, 255],
          "bluegreen": [0, 165, 255],
          "green": [0, 205, 0],
          "red": [255, 0, 0],
          "yellow": [255, 255, 0],
          "purple": [128, 0, 128],
          "neutral": [255, 241, 224]}

disgust_pos = [-0.9, 0]
angry_pos = [-0.5, 0.5]
alert_pos = [0, 0.6]
happy_pos = [0.5, 0.5]
calm_pos = [0.4, -0.4]
relaxed_pos = [0, -0.6]
sad_pos = [-0.5, -0.5]
neu_pos = [0.0, 0.0]

# Each point in the valence/energy map is represented with a static color based
# on the above mapping. All intermediate points of the emotion colormap
# are then computed using the color_map_2d.create_2d_color_map() function:

emo_map = color_map_2d.create_2d_color_map([disgust_pos,
                                            angry_pos,
                                            alert_pos,
                                            happy_pos,
                                            calm_pos,
                                            relaxed_pos,
                                            sad_pos,
                                            neu_pos],
                                           [colors["purple"],
                                            colors["red"],
                                            colors["orange"],
                                            colors["yellow"],
                                            colors["green"],
                                            colors["bluegreen"],
                                            colors["blue"],
                                            colors["neutral"]],
                                           img.shape[0], img.shape[1])
emo_map_img = cv2.addWeighted(img, 0.4, emo_map, 1, 0)


def signal_handler(signal, frame):
    """
    This function is called when Ctr + C is pressed and is used to output the
    final buffer into a WAV file
    """
    # write final buffer to wav file
    """
    if len(all_data) > 1:
        wavfile.write(outstr + ".wav", fs, numpy.int16(all_data))
    """
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def record_audio(block_size, devices, use_yeelight_bulbs=False, fs=8000):

    # initialize the yeelight devices:
    bulbs = []
    if use_yeelight_bulbs:
        for d in devices:
            bulbs.append(Bulb(d))
    try:
        bulbs[-1].turn_on()
    except:
        bulbs = []

    # initialize recording process
    mid_buf_size = int(fs * block_size)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=1, rate=fs,
                     input=True, frames_per_buffer=mid_buf_size)

    mid_buf = []
    count = 0
    global all_data
    global outstr
    all_data = []
    outstr = datetime.datetime.now().strftime("%Y_%m_%d_%I:%M%p")

    # load segment model
    [classifier, mu, std, class_names,
     mt_win, mt_step, st_win, st_step, _] = aT.load_model(load_file("./assets/model"))

    [clf_energy, mu_energy, std_energy, class_names_energy,
     mt_win_en, mt_step_en, st_win_en, st_step_en, _] = \
        aT.load_model(load_file("./assets/energy"))

    [clf_valence, mu_valence, std_valence, class_names_valence,
     mt_win_va, mt_step_va, st_win_va, st_step_va, _] = \
        aT.load_model(load_file("./assets/valence"))


    print("Real time audio mood analysis running ...")

    while 1:
        block = stream.read(mid_buf_size)
        count_b = len(block) / 2
        format = "%dh" % (count_b)
        shorts = struct.unpack(format, block)
        cur_win = list(shorts)
        mid_buf = mid_buf + cur_win
        del cur_win
        if len(mid_buf) >= delay * fs:
            # data-driven time
            x = numpy.int16(mid_buf)
            seg_len = len(x)

            # extract features
            # We are using the signal length as mid term window and step,
            # in order to guarantee a mid-term feature sequence of len 1
            [mt_f, _, _] = mF(x, fs, seg_len, seg_len, round(fs * st_win),
                              round(fs * st_step))
            fv = (mt_f[:, 0] - mu) / std

            # classify vector:
            [res, prob] = aT.classifier_wrapper(classifier, "svm_rbf", fv)
            win_class = class_names[int(res)]
            if prob[class_names.index("silence")] > 0.89:
                soft_valence = 0
                soft_energy = 0
                if args.verbose == 'Y':
                    print("Silence")
                    
                if args.send == 'Y':
                    oscdata = '{"win_class":'+'"Silence"' + \
                                ',"win_class_energy":'+ '"null"' + \
                                ',"win_class_valence":'+'"null"'+ \
                                ',"soft_valence":'+str(soft_valence)+ \
                                ',"soft_energy":'+str(soft_energy)+'}'

                    client.send_message("/WLEDAudioSync/mood/data", oscdata)                    
                    
            else:
                # extract features for music mood
                [f_2, _, _] = mF(x, fs, round(fs * mt_win_en),
                                 round(fs * mt_step_en), round(fs * st_win_en),
                                 round(fs * st_step_en))
                [f_3, _, _] = mF(x, fs, round(fs * mt_win_va),
                                 round(fs * mt_step_va), round(fs * st_win_va),
                                 round(fs * st_step_va))
                # normalize feature vector
                fv_2 = (f_2[:, 0] - mu_energy) / std_energy
                fv_3 = (f_3[:, 0] - mu_valence) / std_valence

                [res_energy, p_en] = aT.classifier_wrapper(clf_energy,
                                                           "svm_rbf",
                                                           fv_2)
                win_class_energy = class_names_energy[int(res_energy)]

                [res_valence, p_val] = aT.classifier_wrapper(clf_valence,
                                                             "svm_rbf",
                                                             fv_3)
                win_class_valence = class_names_valence[int(res_valence)]

                soft_energy = p_en[class_names_energy.index("high")] - \
                              p_en[class_names_energy.index("low")]
                soft_valence = p_val[class_names_valence.index("positive")] - \
                               p_val[class_names_valence.index("negative")]

                if args.verbose == 'Y':
                    print("Data:", win_class, win_class_energy, win_class_valence,
                          soft_valence, soft_energy)
                          
                if args.send == 'Y':
                    oscdata = '{"win_class":"'+ str(win_class) + \
                                '","win_class_energy":"'+ str(win_class_energy) + \
                                '","win_class_valence":"'+str(win_class_valence)+ \
                                '","soft_valence":'+str(soft_valence)+ \
                                ',"soft_energy":'+str(soft_energy)+'}'

                    client.send_message("/WLEDAudioSync/mood/data", oscdata)

            all_data += mid_buf
            mid_buf = []

            h, w, _ = img.shape
            y_center, x_center = int(h / 2), int(w / 2)
            x = x_center + int((w/2) * soft_valence)
            y = y_center - int((h/2) * soft_energy)

            radius = 20
            emo_map_img_2 = emo_map_img.copy()
            color = numpy.median(emo_map[y-2:y+2, x-2:x+2], axis=0).mean(axis=0)
            emo_map_img_2 = cv2.circle(emo_map_img_2, (x, y),
                                       radius,
                                       (int(color[0]), int(color[1]),
                                        int(color[2])), -1)
            emo_map_img_2 = cv2.circle(emo_map_img_2, (x, y),
                                       radius, (255, 255, 255), 2)
            if args.verbose == 'Y':
                print("Color:", int(color[2]), int(color[1]), int(color[0]))
                print(args)
                print('____')
                
            if args.send == 'Y':
                osccolordata = '{"R":'+ str(int(color[2]))+ ',"G":'+ str(int(color[1]))+ ',"B":'+str(int(color[0]))+'}'
                client.send_message("/WLEDAudioSync/mood/color", osccolordata)

            if args.screen == 'Y':
                cv2.imshow('RTMMD Emotion Color Map', emo_map_img_2)

            # set yeelight bulb colors
            if use_yeelight_bulbs:
                for b in bulbs:
                    if b:
                        # attention: color is in bgr so we need to invert:
                        b.set_rgb(int(color[2]), int(color[1]), int(color[0]))

            cv2.waitKey(10)
            count += 1
            # print(count)
            if (count == restart):
                prog_restart()


def parse_arguments():
    record_analyze = argparse.ArgumentParser(description="Real time "
                                                         "audio mood analysis sent via OSC")
    record_analyze.add_argument("-d", "--devices", nargs="+",
                                  help="IPs to Yeelight device(s) to use")
    record_analyze.add_argument("-cs", "--capture", type=int,
                                  choices=range(2,20),
                                  metavar="[2-20]",
                                  default=5, help="Number of second to capture, default to 5")
    record_analyze.add_argument("-bs", "--blocksize",
                                  type=float,
                                  choices=[0.25, 0.5, 0.75, 1],
                                  default=1, help="Recording block size, default to 1")
    record_analyze.add_argument("-fs", "--samplingrate", type=int,
                                  choices=[4000, 8000, 16000, 32000, 44100],
                                  default=8000, help="Sample rate, default to 8KHz")
    record_analyze.add_argument("-sc", "--screen",
                                  choices=['Y','N'],
                                  default='N', help="display color window, default to N")
    record_analyze.add_argument("-srv", "--server",
                                  default='127.0.0.1', help="IP of the OSC server, default to 127.0.0.1")
    record_analyze.add_argument("-p", "--port", type=int,
                                  choices=range(1,65537),
                                  metavar="[1-65536]",
                                  default=12000, help="port number, default to 12000")
    record_analyze.add_argument("-s", "--send",
                                  choices=['Y','N'],
                                  default='Y', help="send to OSC, default to Y")                                  
    record_analyze.add_argument("-v", "--verbose",
                                  choices=['Y','N'],
                                  default='N', help="display verbose informations, default to N")
    record_analyze.add_argument("-r", "--restart", type=int,
                                  choices=range(0,3601),
                                  metavar="[0-3600]",
                                  default=120, help="Number of x * 5s before restarting prog , 0 for never..  default to 120 --> '10 minutes'")
    return record_analyze.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    fs = args.samplingrate
    delay = args.capture
    restart = args.restart
    
    if args.devices:
        devices = args.devices
        use_yeelight_bulbs = True
    else:
        devices = []
        use_yeelight_bulbs = False
        
    if fs != 8000:
        print("Warning! Segment classifiers have been trained on 8KHz samples."
              " Therefore results will be not optimal. ")
    if delay != 5:
        print("Warning! Default record value changed."
              " Therefore results will be not optimal, especially if < 5. ")

    if args.send == 'Y':
        client = udp_client.SimpleUDPClient(args.server, args.port)
              
    record_audio(args.blocksize, devices, use_yeelight_bulbs, fs)
