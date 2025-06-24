# ==============================================================================
# Labour Hire Command Centre - Flask Web Server v2.0
#
# Description:
# This script uses the Flask web framework to turn the Command Centre's
# functions into a real API, creating a robust backend for the web app.
# ==============================================================================

import os
import json
from flask import Flask, request, jsonify, render_template
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults

# --- Flask App Initialization ---
# This tells Flask to look for your HTML file in a 'templates' folder.
app = Flask(__name__, template_folder='templates')

# --- API Key Configuration ---
# Your keys are placed here directly for simplicity.
os.environ["GOOGLE_API_KEY"] = "AIzaSyBKnGRM3G79dZfdVMAsJIej2s5tCFxXPIw"
os.environ["TAVILY_API_KEY"] = "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"


# --- Data (Simulated Database) ---
CANDIDATE_DATABASE = """
    Name: John Smith, Role: General Labourer, Skills: Site cleanup, Fencing, Assisting trades, Tickets: White Card, First Aid, Availability: Mon-Fri, Contact: 0411111111
    Name: David Jones, Role: Scaffolder, Skills: Advanced scaffolding, Reading plans, Team lead, Tickets: Advanced Scaffolding Ticket, Working at Heights, EWP, Availability: Mon-Sat, Contact: 0422222222
    Name: Michael Chen, Role: Crane Operator / Dogman, Skills: Operating 25t Franna, Rigging, Slinging loads, Tickets: Dogman Ticket, C6 Crane License, White Card, Availability: Tue-Sat, Contact: 0433333333
    Name: Sarah Williams, Role: General Labourer, Skills: Traffic control, Using power tools, Tickets: White Card, Traffic Control Ticket, Availability: Mon,Wed,Fri, Contact: 0444444444
    Name: Kyle Hurley, Role: Formwork Labourer / Dogman, Skills: Concreting, Formwork, Dogging crane, Tickets: White Card, Dogman Ticket, Availability: Any Day, Contact: 0447065559
"""

# --- AI Initialization ---
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    search_tool = TavilySearchResults(max_results=10)
    print("✅ AI Models Initialized Successfully.")
except Exception as e:
    print(f"❌ Critical Error: Failed to initialize AI models. Check API keys. Error: {e}")
    llm = None
    search_tool = None

# --- API Endpoints ---

@app.route('/')
def index():
    # This serves your main HTML page from the 'templates' folder.
    return render_template('index.html')

@app.route('/api/find-client', methods=['POST'])
def find_client():
    if not llm: return jsonify({"error": "AI model not initialized"}), 500
    data = request.get_json()
    if not data or 'query' not in data: return jsonify({"error": "Missing 'query' in request body"}), 400
    
    query = data['query']
    try:
        search_context = search_tool.invoke(f"{query} phone number")
        prompt = f"""You are a data extraction service. Analyze the following text from web search results and extract a list of companies and their real Australian phone numbers.
        RULES:
        1. Your goal is to extract a maximum of 5 high-quality leads.
        2. You MUST find an associated Australian phone number for each company WITHIN THE PROVIDED TEXT.
        3. CRITICAL: If you cannot find a real phone number for a company IN THE TEXT, DISCARD IT. Do not invent information.
        4. Format the output as a clean, numbered list. Do not add commentary.

        Here is the text to analyze: --- {json.dumps(search_context)} --- Final Answer:"""
        response = llm.invoke(prompt)
        return jsonify({"response": response.content})
    except Exception as e:
        print(f"Error in /find-client: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/find-worker', methods=['POST'])
def find_worker():
    if not llm: return jsonify({"error": "AI model not initialized"}), 500
    data = request.get_json()
    if not data or 'query' not in data: return jsonify({"error": "Missing 'query' in request body"}), 400
    
    query = data['query']
    try:
        prompt = f"""You are a recruitment assistant. Your task is to search the provided list of candidates to find the best match for a user's request.
        Analyze the user's request and the candidate list, then provide the name and details of the single best matching candidate. If no one is a good match, state that clearly.
        User Request: "{query}"
        Available Candidate List: --- {CANDIDATE_DATABASE} --- Final Answer:"""
        response = llm.invoke(prompt)
        return jsonify({"response": response.content})
    except Exception as e:
        print(f"Error in /find-worker: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scout-talent', methods=['POST'])
def scout_talent():
    if not llm: return jsonify({"error": "AI model not initialized"}), 500
    data = request.get_json()
    if not data or 'query' not in data: return jsonify({"error": "Missing 'query' in request body"}), 400
    
    query = data['query']
    try:
        specific_query = f`site:facebook.com "brisbane jobs" OR "sunshine coast jobs" OR "nsw jobs" OR "australia tradies" "{query} looking for work"`
        search_context = search_tool.invoke(specific_query)
        
        prompt = f"""You are a talent scout. Your job is to analyze the following text from web search results, which are from Facebook groups.
        Your only goal is to identify individuals advertising their trade skills.
        RULES:
        1. Extract the person's name (if it's clearly an individual's name).
        2. Extract the direct URL to the Facebook post.
        3. Ignore all company job advertisements, links to other websites, or general group discussions. Focus ONLY on posts from individuals looking for work.
        4. If no individuals are found, state that clearly.
        5. Format the output as a clean, numbered list: Name - Post URL.
        TEXT TO ANALYZE: --- {json.dumps(search_context)} --- Final Answer:"""
        
        response = llm.invoke(prompt)
        return jsonify({"response": response.content})
        
    except Exception as e:
        print(f"Error in /scout-talent: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # This runs the web server. For deployment, a production server like Gunicorn is recommended.
    app.run(host='0.0.0.0', port=5001, debug=True)
