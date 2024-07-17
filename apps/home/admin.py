import json
import os
from apps.home import blueprint
from flask import (
    Blueprint,
    jsonify,
    request,
)



@blueprint.route('/get_intents', methods=['GET'])
def get_intents():
    with open('intents3.json', 'r') as f:
        intents = json.load(f)
    return jsonify(intents)

@blueprint.route('/update_intent', methods=['POST'])
def update_intent():
    data = request.json
    with open('intents3.json', 'r') as f:
        intents = json.load(f)
    
    # Update the intent
    for intent in intents['intents']:
        if intent['tag'] == data['tag']:
            intent.update(data)
            break
    
    with open('intents3.json', 'w') as f:
        json.dump(intents, f, indent=4)
    
    return jsonify({"status": "success"})

@blueprint.route('/add_intent', methods=['POST'])
def add_intent():
    new_intent = request.json
    with open('intents3.json', 'r') as f:
        intents = json.load(f)
    
    intents['intents'].blueprintend(new_intent)
    
    with open('intents3.json', 'w') as f:
        json.dump(intents, f, indent=4)
    
    return jsonify({"status": "success"})

@blueprint.route('/delete_intent', methods=['POST'])
def delete_intent():
    tag = request.json['tag']
    with open('intents3.json', 'r') as f:
        intents = json.load(f)
    
    intents['intents'] = [intent for intent in intents['intents'] if intent['tag'] != tag]
    
    with open('intents3.json', 'w') as f:
        json.dump(intents, f, indent=4)
    
    return jsonify({"status": "success"})

@blueprint.route('/retrain', methods=['POST'])
def retrain():
    os.system('python train.py')
    return jsonify({"status": "success"})

if __name__ == '__main__':
    blueprint.run(debug=True)