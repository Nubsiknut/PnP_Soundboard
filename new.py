#!/usr/bin/env python

import glob

import PyAudio
import wave

from flask import Flask, redirect, url_for

app = Flask(__name__)
loud_devices = [u'Display Audio',
                u'Built-in Output'
                ]


class WaveReader(object):
    def __init__(self, filename, size=1024):
        self.wav = wave.open(filename, 'rb')
        self.size = size

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback) :
        self.wav.close()
        if value: raise

    def __iter__(self):
        data = self.wav.readframes(self.size)
        while data != '':
            yield data
            data = self.wav.readframes(self.size)
        raise StopIteration

    @property
    def getframerate(self):
        return self.wav.getframerate()

    @property
    def getnchannels(self):
        return self.wav.getnchannels()

    @property
    def getsampwidth(self):
        return self.wav.getsampwidth()


class PlayLoud(object):
    def __init__(self, loud_devices):
        self.pya = pyaudio.PyAudio()
        self.loud_devices = loud_devices

    @property
    def output_devices(self):
        for idx in self.output_device_indexes:
            yield self.pya.get_device_info_by_index(idx).get('name', 'unknown'), idx

    @property
    def output_device_indexes(self):
        for i in range(self.pya.get_device_count()):
            dev = self.pya.get_device_info_by_index(i)
            if dev.get('maxOutputChannels', 0) > 0:
                yield i

    @property
    def output_device_names(self):
        for idx in self.output_device_indexes:
            yield self.pya.get_device_info_by_index(idx).get('name', 'unknown')


    @property
    def loud_output(self):
        output_devices = {name:idx for name, idx in self.output_devices}
        for name in self.loud_devices:
            if name in output_devices:
                return name, output_devices[name]

    @property
    def loud_output_index(self):
        _, idx = self.loud_output
        return idx

    @property
    def loud_output_name(self):
        name, _ = self.loud_output
        return name

    def play_wav(self, filename, output_device_index):
        wav = WaveReader(filename)
        stream = self.pya.open(
            format = self.pya.get_format_from_width(wav.getsampwidth),
            channels = wav.getnchannels,
            rate = wav.getframerate,
            output = True,
            output_device_index = output_device_index)

        with wav as data:
            for datum in data:
                stream.write(datum)

        stream.close()



@app.route("/")
def index():
    filenames = glob.glob('*.mp3')
    page=""
    for name in filenames:
        page += "<a href='/play/%s'>%s</a><br/><br/>"% (name,name)
    return page


@app.route("/play/<name>")
def play(name):
    pl = PlayLoud(loud_devices)
    pl.play_wav(name, pl.loud_output_index)
    return redirect(url_for('index'))


def main():
    pl = PlayLoud(loud_devices)
    print ('{} : {}'.format(pl.loud_output_name, ' '.join(pl.output_device_names)))
    app.debug = True
    app.run(host='127.0.0.1', port=8080)


if __name__ == '__main__':
    main()
