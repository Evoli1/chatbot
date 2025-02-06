import os
import requests
from flask import Flask, render_template, request, jsonify
import openai
import logging
import time
from PyPDF2 import PdfReader

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Path to the knowledge PDF
KNOWLEDGE_PDF_PATH = "static/knowledge.pdf"  # Path to the PDF file

# Function to extract text from the PDF
def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        # Clean and preprocess the text (optional step)
        text = text.replace("\n", " ").strip()
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None

# Preload the knowledge base (extract content from the PDF once at the start)
knowledge_text = extract_text_from_pdf(KNOWLEDGE_PDF_PATH)
if not knowledge_text:
    logging.error("Failed to load knowledge base from PDF. Exiting...")
    exit()

def get_openai_answer(context, question):
    try:
        completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": f"Search and give a short german information about {question} in the {context}. Use emoji and du instead of Sie. If the {question} is not about library, say appologize that you cannot help."
                    }
                ]
            )
        answer =  (completion['choices'][0]['message']['content'])
        return answer
    except openai.error.OpenAIError as e:
        logging.error(f"Error with OpenAI API: {e}")
        return "Entschuldigung, es gab ein Problem bei der Verarbeitung deiner Anfrage."
    
def get_openai_description(book_title):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing short German introductions for books."},
                {"role": "user", "content": f"Gib eine kurze deutsche Einführung in einem Satz für das Buch '{book_title}'."}
            ]
        )
        return completion['choices'][0]['message']['content']
    except openai.error.OpenAIError as e:
        logging.error(f"Error generating book description: {e}")
        return f"Entschuldigung, ich konnte keine Einführung für '{book_title}' erstellen."

    

# Function to generate a natural follow-up question
def get_follow_up_question():
    try:
        follow_up = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly and natural-sounding chatbot."},
                {"role": "user", "content": "Ask the user in German if they have further questions. Use du not Sie. Be more creative than something just hast du weitere Fragen"}
            ]
        )
        follow_up_question = follow_up['choices'][0]['message']['content']
        return follow_up_question
    except openai.error.OpenAIError as e:
        logging.error(f"Error generating follow-up question: {e}")
        return "Hast du noch weitere Fragen? 😊"
    
# Function to check if the user's input is a positive response
def is_positive_response(user_input):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that determines if a german user's response implies 'yes' in any context."},
                {"role": "user", "content": f"Does the following german text imply 'yes' in any way: '{user_input}'? Answer with 'yes' or 'no' only. If {user_input} is 'ja', answer with 'yes'"}
            ]
        )
        response = completion['choices'][0]['message']['content'].strip().lower()
        return response == "yes"
    except openai.error.OpenAIError as e:
        logging.error(f"Error determining positive response: {e}")
        return False

# Function to check if the user's input means "no"
def is_negative_response(user_input):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that determines if a german user's response implies 'no' in any context."},
                {"role": "user", "content": f"Does the german following text mean 'no' in any sense: '{user_input}'? Answer with 'yes' or 'no' only."}
            ]
        )
        response = completion['choices'][0]['message']['content'].strip().lower()
        return response == "yes"
    except openai.error.OpenAIError as e:
        logging.error(f"Error determining negative response: {e}")
        return False

# Global variable to track user query and results
user_session_data = {"query": None, "results": [], "current_index": 0}

import time
import logging
import requests

def search_books(query):
    google_books_api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10"
    max_retries = 5  # Max retries before giving up
    retry_delay = 5  # Delay in seconds between retries

    for attempt in range(max_retries):
        try:
            response = requests.get(google_books_api_url)
            response.raise_for_status()  # Will raise an error for status codes 4xx/5xx
            data = response.json()

            books = []
            for item in data.get("items", []):
                book_info = item.get("volumeInfo", {})
                title = book_info.get("title", "No title available")
                authors = book_info.get("authors", ["No authors available"])
                book_type = book_info.get("printType", "No type available")
                publisher = book_info.get("publisher", "No publisher available")
                isbn = None
                for identifier in book_info.get("industryIdentifiers", []):
                    if identifier.get("type") == "ISBN_13":
                        isbn = identifier.get("identifier")
                        break
                    elif identifier.get("type") == "ISBN_10":
                        isbn = identifier.get("identifier")
                        break
                image_link = book_info.get("imageLinks", {}).get("thumbnail", "")

                books.append({
                    "title": title,
                    "authors": authors,
                    "type": book_type,
                    "publisher": publisher,
                    "isbn": isbn,
                    "image_link": image_link
                })

            return books
        
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:
                logging.warning(f"Rate limit exceeded: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)  # Wait before retrying
            else:
                logging.error(f"Error fetching books from Google Books API: {e}")
                break

    # If we exhaust all retries, return an empty list
    return []


    
@app.route('/')
def index():
    return render_template('index.html')

    
@app.route('/chat', methods=['POST'])
def chat():
    global user_session_data
    user_input = request.form['user_input'].strip().lower()

    time.sleep(1)  # Delay for 1 second

    if user_input == "literatur-suchen":
        user_session_data = {"mode": "literatur-suchen", "query": None, "results": [], "current_index": 0}
        return jsonify({'response': 'Gib mir bitte den Buchtitel, den Namen des Autors oder die ISBN ein, um mit der Suche zu beginnen.'})
    
    elif user_input == "literatur-vorschlagen":
        user_session_data = {"mode": "literatur-vorschlagen", "query": None, "results": [], "current_index": 0}
        return jsonify({'response': 'Erzähl mir einfach, was du gerne lesen möchtest oder ob es ein bestimmtes Thema gibt, das dich interessiert. Ich helfe dir gerne dabei, das perfekte Buch zu finden! 😊'})
    
    elif user_input == "information-request":
        user_session_data = {"mode": "information-request", "query": None, "results": [], "current_index": 0}
        return jsonify({'response': 'Ich kann dir mit Informationen über die Öffnungszeiten oder die Bibliotheksrichtlinien helfen. Was genau suchst du?'})
    
    elif is_negative_response(user_input):
        mode = user_session_data.get("mode")
        
        if mode == "information-request":
            return jsonify({'response': "Vielen Dank für deine Zeit! Du kannst auf die Schaltfläche 'Schließen' klicken, um den Chat zu beenden. 😊"})
        
        elif mode in ["literatur-suchen", "literatur-vorschlagen"]:
            user_session_data = {"mode": "close-mode", "query": None, "results": [], "current_index": 0}
            return jsonify({'response': "Möchtest du noch etwas wissen oder kann ich dir sonst irgendwie weiterhelfen?"})
        elif mode == "close-mode":
            return jsonify({'response': "Danke fürs Chatten! Ich hoffe, du hast ein tolles Buch gefunden. Viel Spaß beim Lesen und bis bald! 📚😊"})
        
    elif is_positive_response(user_input):
        mode = user_session_data.get("mode")

        if mode == "literatur-suchen":
            # If the user said something positive, show more results
            start_index = user_session_data["current_index"]
            user_session_data["current_index"] += 3
            books = user_session_data["results"][start_index:user_session_data["current_index"]]

            if books:
                response_after_books = "Möchtest du noch mehr sehen?"  # Ask if they want more results
                return jsonify({'response': "📚 Hier sind weitere Suchergebnisse:", 'books': books, 'response_after_books': response_after_books})
            else:
                return jsonify({'response': "Es gibt keine weiteren Ergebnisse."})
            
        elif mode == "literatur-vorschlagen":
            # If the user said something positive, show more results
            start_index = user_session_data["current_index"]
            user_session_data["current_index"] += 3
            books = user_session_data["results"][start_index:user_session_data["current_index"]]

            if books:
                descriptions = [
                    get_openai_description(book["title"]) for book in books
                ]
                response = "📚 Hier sind weitere Vorschläge:"
                return jsonify({'response': response, 'books': books, 'descriptions': descriptions, 'response_after_books': "Möchtest du noch weitere Vorschläge sehen?"})
            else:
                return jsonify({'response': "Entschuldigung, ich habe keine Bücher gefunden."})
    else:
        mode = user_session_data.get("mode")
        if mode == "literatur-suchen":
            user_session_data["query"] = user_input
            user_session_data["results"] = search_books(user_input)
            user_session_data["current_index"] = 3
            books = user_session_data["results"][:3]

            if books:
                response = "📚 Hier sind die ersten drei Suchergebnisse, die ich für dich gefunden habe:"
                response_after_books = "Möchtest du weitere Ergebnisse sehen?"  # New message after showing results
                return jsonify({'response': response, 'books': books, 'response_after_books': response_after_books})
            else:
                return jsonify({'response': "Entschuldigung, ich habe keine Bücher gefunden."})
        elif mode == "literatur-vorschlagen":
            user_session_data["query"] = user_input
            user_session_data["results"] = search_books(user_input)  
            user_session_data["current_index"] = 3
            books = user_session_data["results"][:3]  

            if books:
                descriptions = [
                    get_openai_description(book["title"]) for book in books
                ]
                response = "📚 Hier sind drei Vorschläge:"
                return jsonify({'response': response, 'books': books, 'descriptions': descriptions, 'response_after_books': "Möchtest du noch weitere Vorschläge sehen?"})
            else:
                return jsonify({'response': "Entschuldigung, ich habe keine Bücher gefunden."})
            
        elif mode == "information-request":
            try:
                answer = get_openai_answer(knowledge_text, user_input)
                response = answer if answer else "Entschuldigung, ich konnte keine relevante Antwort finden."

                # Set follow-up pending and include follow-up flag in response
                user_session_data['follow_up_pending'] = True

                return jsonify({'response': response, 'follow_up': True})  # Include follow-up flag
            except Exception as e:
                logging.error(f"Error processing OpenAI API: {e}")
                response = "Entschuldigung, es gab ein Problem bei der Verarbeitung deiner Anfrage."
            return jsonify({'response': response, 'follow_up': False})  # Ensure follow_up is False if there's an error

        else:
            return jsonify({'response': "Bitte starte eine neue Anfrage."})




@app.route('/follow_up', methods=['POST'])
def follow_up():
    # Ensure a follow-up question is needed
    if not user_session_data.get('follow_up_pending', False):
        return jsonify({'response': "Kein Follow-up erforderlich."})

    try:
        # Generate the follow-up question
        follow_up_question = get_follow_up_question()  # Implement or call OpenAI API to create a follow-up question
        user_session_data['follow_up_pending'] = False  # Reset the flag
        return jsonify({'response': follow_up_question})
    except Exception as e:
        logging.error(f"Error generating follow-up question: {e}")
        return jsonify({'response': "Hast du noch weitere Fragen? "})

if __name__ == "__main__":
    app.run(debug=True)
