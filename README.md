# Flask Chatbot

A simple chatbot built using Flask and OpenAI's API.

🚀 Installation
Follow these steps to set up the project:

1️⃣ Clone the Repository
git clone https://github.com/your-username/your-repo.git
cd your-repo

2️⃣ Create and Activate a Virtual Environment
// Create a virtual environment
python -m venv venv
// Activate the virtual environment
// On Windows:
venv\Scripts\activate
// On macOS/Linux:
source venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

🔑 Add OpenAI API Key
Before running the application, set your OpenAI API key as an environment variable.
export OPENAI_API_KEY="your-api-key"  # For macOS/Linux
set OPENAI_API_KEY="your-api-key"     # For Windows (CMD)
$env:OPENAI_API_KEY="your-api-key"    # For Windows (PowerShell)

▶️ Running the Application
Once everything is set up, run the Flask app:
python app.py

Your chatbot should now be running on http://127.0.0.1:5000/.

📌 Notes
Ensure you have Python 3.7+ installed.
If you face any issues, check the dependencies and API key.

