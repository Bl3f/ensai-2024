from flask import Flask, request, jsonify
import joblib
import os
import requests

app = Flask(__name__)
regr = joblib.load("model.v1.bin")
LLM_API = os.getenv("LLM_API")


def encode_prenom(prenom: str):
    """
        This function encode a given name into a pd.Series.

        For instance alain is encoded [1, 0, 0, 0, 0 ... 1, 0 ...].
    """
    alphabet = "abcdefghijklmnopqrstuvwxyzé-'"
    prenom = prenom.lower()

    return [int(letter in prenom) for letter in alphabet]


@app.route("/predict")
def predict():
    name = request.args.get("name")
    model = request.args.get("model")

    if name:
        if model is None or model != 'llm':
            sexe = regr.predict([encode_prenom(name)])
            response = {
                "name": name,
                "gender": 'M' if sexe[0] == 0 else 'F',
            }
        else:
            prompt = f"""
                What's the gender of the name ${name}?
                Instructions:
                - Give me the response in only one character. 
                - For instance 'M' for male and 'F' for female. 
                - This is important you give me the anwser in only 1 character and not more.
                - Expected answer "M" or "F"
            """
            url = f"{LLM_API}/api/generate"
            llm_response = requests.post(url, json={"model": "mistral", "prompt": prompt, "stream": False})
            sexe = llm_response.json()["response"].strip()

            response = {
                "name": name,
                "gender": sexe[0],
                "debug": llm_response.text,
                "url": url,
            }


        return jsonify(response)
    else:
        return jsonify({"error": "You need to pass name as GET parameter."})
