from music21 import converter, instrument, note, chord
import sys
import numpy as np
from PIL import Image
from imageio import imwrite

def extractNote(element):
    return int(element.pitch.ps)

def extractDuration(element):
    return element.duration.quarterLength

def get_notes(notes_to_parse):

    """ Get all the notes and chords from the midi files in the ./midi_songs directory """
    durations = []
    notes = []
    start = []

    for element in notes_to_parse:
        if isinstance(element, note.Note):
            if element.isRest:
                continue

            start.append(element.offset)
            notes.append(extractNote(element))
            durations.append(extractDuration(element))
                
        elif isinstance(element, chord.Chord):
            if element.isRest:
                continue
            for chord_note in element:
                start.append(element.offset)
                durations.append(extractDuration(element))
                notes.append(extractNote(chord_note))

    return {"start":start, "pitch":notes, "dur":durations}

def is_empty(list):
    for item in list:
        if item != 0:
            return False
    return True

def midi2image(midi_path, resolution = 0.025, upperBoundNote = 127, maxSongLength = 100):
    mid = converter.parse(midi_path, quantizePost=False, makeNotation=False)

    instruments = instrument.partitionByInstrument(mid)

    data = {}

    try:
        i=0
        for instrument_i in instruments.parts:
            notes_to_parse = instrument_i.recurse()

            notes_data = get_notes(notes_to_parse)
            if len(notes_data["start"]) == 0:
                continue

            if instrument_i.partName is None:
                data["instrument_{}".format(i)] = notes_data
                i+=1
            else:
                data[instrument_i.partName] = notes_data

    except:
        notes_to_parse = mid.flat.notes
        data["instrument_0"] = get_notes(notes_to_parse)

    for instrument_name, values in data.items():
        # https://en.wikipedia.org/wiki/Scientific_pitch_notation#Similar_systems

        pitches = values["pitch"]
        durs = values["dur"]
        starts = values["start"]

        matrix = np.zeros((maxSongLength, upperBoundNote))
        
        np.set_printoptions(threshold=sys.maxsize)

        for dur, start, pitch in zip(durs, starts, pitches):
            dur = int(dur/resolution)
            start = int(start/resolution)

            if not start > 0 or not dur+start < 0:
                for j in range(start,start+dur):
                    if j  >= 0 and j  < maxSongLength:
                        matrix[j, pitch] = 255

        if matrix.any(): # If matrix contains no notes (only zeros) don't save it
            trimmed_list = matrix
            # trim back
            while is_empty(trimmed_list[-1]):
                trimmed_list = trimmed_list[:-1]
            
            # trim front
            while is_empty(trimmed_list[0]):
                trimmed_list = trimmed_list[1:]
            
            imwrite("export/image.png",np.matrix(np.array(trimmed_list)).astype(np.uint16))
            im = Image.open("export/image.png")
            im = im.rotate(90, expand=True)
            im = im.resize((7680,212))
            im.show()
            im.save('export/rotated.png')
        else:
            break

if __name__ == "__main__":
    midi_path = sys.argv[1]

    if len(sys.argv) >= 3:
        max_repetitions = int(sys.argv[2])
        midi2image(midi_path, max_repetitions, maxSongLength=500000)
    else:
        midi2image(midi_path, maxSongLength=500000)
