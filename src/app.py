import json
from pydub import AudioSegment
import whisper
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

def convert_wav_to_text(src):
    """Convert WAV file to text using Whisper."""
    model = whisper.load_model("base")
    result = model.transcribe(src)
    return result['text']

def load_phishing_words():
    """Load phishing words from a JSON file."""
    with open('phishing_words.json', 'r') as file:
        phishing_words = json.load(file)
    return phishing_words

def check_for_phishing_words(text, phishing_words):
    """Check the text for phishing words and calculate statistics."""
    phishing_count = 0
    sentences = text.split('.')
    total_sentences = len(sentences)
    
    for sentence in sentences:
        for word in phishing_words:
            if word.lower() in sentence.lower():
                phishing_count += 1
                break  # Only count the sentence once, even if multiple phishing words are found

    phishing_percentage = (phishing_count / total_sentences) * 100 if total_sentences > 0 else 0
    return phishing_count, total_sentences, phishing_percentage

@app.route('/predict', methods=['POST'])
def predict():
    if 'audio' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    audio_file = request.files['audio']
    
    # Save the uploaded file to a temporary location
    audio_path = "temp_upload.wav"
    audio_file.save(audio_path)
    
    try:
        transcript_text = convert_wav_to_text(audio_path)
        os.remove(audio_path)  # Clean up the temporary file

        if transcript_text:
            # Load phishing words
            phishing_words = load_phishing_words()
            phishing_count, total_sentences, phishing_percentage = check_for_phishing_words(transcript_text, phishing_words)

            return jsonify({
                "Total sentences": total_sentences,
                "Phishing sentences": phishing_count,
                "Phishing percentage": phishing_percentage
            })
        else:
            return jsonify({"error": "Transcription failed"}), 500
    except Exception as e:
        os.remove(audio_path)  # Clean up the temporary file in case of error
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
