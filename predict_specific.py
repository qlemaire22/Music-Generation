import numpy
from music21 import instrument, note, stream, chord
import network
import data
import argparse
import config
from tools import listenToMidi
from vae import vae_predict
import numpy as np

RUN_NAME = "run4"
WEIGHT_NAME = "weights-0.2561.hdf5"
conditions = ["mexico", "xinhua"]


def generate(i):
    """ Generate a piano midi file """

    states = vae_predict.generate()

    h1, c1, h2, c2, h3, c3 = np.split(states.T, 6)

    _, _, n_vocab, pitchnames, _ = data.prepare_sequences()
    _, _, _, _, network_input = data.prepare_sequences(conditions=conditions)

    net = network.NetworkWithInit(n_vocab, h1, c1, h2, c2, h3, c3)
    model = net.model
    model.load_weights("results/" + RUN_NAME + "/" + WEIGHT_NAME)
    prediction_output, network_output = generate_notes(model, list(
        network_input), list(pitchnames), n_vocab)

    conditions_string = ""
    n = len(conditions)

    for j in range(n):
        conditions_string += conditions[j]
        conditions_string += "_"

    if conditions_string == "":
        conditions_string = "all"

    print("Generate songs for:" + conditions_string)

    np.save("results/" + RUN_NAME +
            "/" + conditions_string + 'output' + str(i) + '.npy', network_output)
    return create_midi(prediction_output, i)


def generate_notes(model, network_input, pitchnames, n_vocab):
    """ Generate notes from the neural network based on a sequence of notes """
    # pick a random sequence from the input as a starting point for the prediction
    start = numpy.random.randint(0, len(network_input) - 1)

    int_to_note = dict((number, note)
                       for number, note in enumerate(pitchnames))

    pattern = list(network_input[start])
    prediction_output = []
    network_output = []

    # generate 500 notes
    for note_index in range(config.GENERATION_LENGTH):
        prediction_input = numpy.reshape(pattern, (1, len(pattern), 1))
        prediction_input = prediction_input / float(n_vocab)

        prediction = model.predict(prediction_input, verbose=0)

        index = numpy.argmax(prediction)
        network_output.append(index)
        result = int_to_note[index]
        prediction_output.append(result)

        pattern.append(index)
        pattern = pattern[1:len(pattern)]

    return prediction_output, network_output


def create_midi(prediction_output, i):
    """ convert the output from the prediction to notes and create a midi file
        from the notes """
    offset = 0
    output_notes = []

    conditions_string = ""
    n = len(conditions)

    for j in range(n):
        conditions_string += conditions[j]
        conditions_string += "_"

    if conditions_string == "":
        conditions_string = "all"

    # create note and chord objects based on the values generated by the model
    for pattern in prediction_output:
        # pattern is a chord
        if ('.' in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split('.')
            notes = []
            for current_note in notes_in_chord:
                new_note = note.Note(int(current_note))
                new_note.storedInstrument = instrument.Piano()
                notes.append(new_note)
            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            output_notes.append(new_chord)
        # pattern is a note
        else:
            new_note = note.Note(pattern)
            new_note.offset = offset
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)

        # increase offset each iteration so that notes do not stack
        offset += 0.5

    midi_stream = stream.Stream(output_notes)

    midi_stream.write('midi', fp="results/" + RUN_NAME +
                      "/" + conditions_string + 'output' + str(i) + '.mid')
    return "results/" + RUN_NAME + "/" + conditions_string + 'output' + str(i) + '.mid'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--number', default=1,
                        help="int, number of music you want to generate.", type=int)
    parser.add_argument('--listen', default=0,
                        help="int, 1 to listen to the song directly with python after generation.", type=int)

    args = parser.parse_args()

    for i in range(args.number):
        print("Generation MIDI " + repr(i))
        filename = generate(i)
        print("... Done, ", filename)
        if args.listen == 1:
            listenToMidi(filename)
