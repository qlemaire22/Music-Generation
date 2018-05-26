import network
import data
import preprocessing
import numpy as np
from keras.callbacks import ModelCheckpoint
from tqdm import tqdm
import config
from keras.callbacks import CSVLogger
import os

conditions = ["island"]
RUN_NAME = "run4"
WEIGHT_NAME = "weights-0.2561.hdf5"

def init():
    """ Train a Neural Network to generate music """

    _, _, n_vocab, _, _ = data.prepare_sequences()
    network_input, _, _, _, _ = data.prepare_sequences(conditions = conditions)

    net = network.NetworkGetStates(n_vocab)
    model = net.model

    if not os.path.exists("outputs/states"):
        os.makedirs("outputs/states")

    model.load_weights("results/" + RUN_NAME + "/" + WEIGHT_NAME)

    generate_states(model, network_input)

def generate_states(model, network_input):
    """ generate states """

    states = np.zeros((config.NUMBER_GENERATED_STATES, 512*6))

    for i in tqdm(range(config.NUMBER_GENERATED_STATES)):
        _, state1, state2, state3, state4, state5, state6 = model.predict(network_input, verbose=0)
        state = np.concatenate((state1[-1].T, state2[-1].T, state3[-1].T, state4[-1].T, state5[-1].T, state6[-1].T))
        states[i] = state

    conditions_string = ""
    n = len(conditions)

    for i in range(n):
        conditions_string += conditions[i]
        conditions_string += "_"

    if conditions_string == "":
        conditions_string = "all"

    np.save("outputs/states/" + conditions_string + "states.npy", states)

if __name__ == '__main__':
    init()
