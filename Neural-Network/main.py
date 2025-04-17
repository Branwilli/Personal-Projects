#Import Libraries
import numpy
import tensorflow
from tensorflow.keras import layers, models 
from tensorflow.keras.models import load_model 
import random 
import json 
import pickle
import nltk 
from nltk.stem.lancaster import LancasterStemmer
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

stemmer = LancasterStemmer() #Creates an instance of Lancaster Stemmer 

#loads intents file 
with open("intents.json") as file:
    data = json.load(file)

#Process Data
try:
    with open("data.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f)

#Exception for when data cannot be found        
except Exception as e:
    print(f"Error loading data: {e}")

    words = []
    labels = []
    docs_x = []
    docs_y = []

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            wrds = nltk.word_tokenize(pattern) #breaks apart string text into individual text
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"] #Creates a list of root words
    words = sorted(list(set(words)))
    labels = sorted(labels)

    #training data preparation 
    training = []
    output = []
    out_empty = [0 for _ in range(len(labels))]

    for x, doc in enumerate(docs_x):
        bag = []
        wrds = [stemmer.stem(w) for w in doc]

        for w in words: 
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)
        
        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)

    training = numpy.array(training)
    output = numpy.array(output)

    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)

tensorflow.keras.backend.clear_session()

#Creates neural network model 
model = models.Sequential()
model.add(layers.Input(shape=(46,)))
model.add(layers.Dense(32, activation='relu'))
model.add(layers.Dense(16, activation='relu'))
model.add(layers.Dense(6, activation='softmax'))

#Save and load model
try:
    model = load_model("model.keras")

except Exception as e:
    print(f"Error loading model: {e}")
    
    model.compile(optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy'])

    model.fit(training, output, epochs=1000, batch_size=8)
    model.save("model.keras")
    #model.summary()

#Convert user input into a bag-of-words vector for the model
def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]
    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for n in s_words:
        for i, x in enumerate(words):
            if x in n:
                bag[i] = 1
    return numpy.array(bag)

#Chat Function
@app.route('/api/chat', methods=['POST'])
def chat():
    #print("Weclome, start interacting with the bot! (type quit to exit)")
    #while True:
        #inp = input("You: ")
    try:
        user_input = request.json.get('message', '')
        if user_input.lower() == "quit":
            return jsonify({'response': 'Chat session ended', 'end_session': True})

        input_data = bag_of_words(user_input, words)
        output_data = model.call(input_data[None, :])[0]
        output_index = numpy.argmax(output_data)
        tag = labels[output_index]

        if output_data[output_index] > 0.7:
            for tg in data["intents"]:
                if tg['tag'] == tag:
                    responses = tg['responses']
            bot_response = random.choice(responses)

        else: 
            bot_response = "Sorry, I didn't get that. Could you rephrase the question?"

        return jsonify({
            'response': bot_response,
            'tag': tag,
            'confidence': float(output_data[output_index])
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
