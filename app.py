from flask import Flask, render_template, request
from groq import Groq  
import os
import re

app = Flask(__name__)

def format_response_to_points(text):
    """Convert paragraph text to bullet points with better structure detection"""
    if not text.strip():
        return text

    # Clean up the text first
    text = text.strip()
    
    # Split by major sections (headers, numbered lists, etc.)
    sections = re.split(r'(?=^[A-Z][^.!?]*$|^[0-9]+\.|^[A-Z][a-z]+:|^[A-Z\s]+$)', text, flags=re.MULTILINE)
    
    formatted_points = []
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # Check if this is a header
        if re.match(r'^[A-Z][^.!?]*$|^[0-9]+\.|^[A-Z][a-z]+:|^[A-Z\s]+$', section.strip(), re.MULTILINE):
            # This is a header, add it as a separate point
            formatted_points.append(f"<strong>{section.strip()}</strong>")
        else:
            # This is content, split into sentences and group logically
            sentences = re.split(r'(?<=[.!?])\s+', section.strip())
            current_point = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Start new point if:
                # 1. Current point is getting too long (>150 chars)
                # 2. Sentence starts with specific keywords
                # 3. Sentence contains bullet indicators
                if (len(current_point) > 150 or
                    sentence.startswith(('* ', '- ', '• ', '1. ', '2. ', '3. ')) or
                    re.match(r'^[A-Z][a-z]+:', sentence)):
                    
                    if current_point:
                        formatted_points.append(current_point.strip())
                    current_point = sentence
                else:
                    if current_point:
                        current_point += " " + sentence
                    else:
                        current_point = sentence
            
            # Add the last point
            if current_point:
                formatted_points.append(current_point.strip())
    
    # Format as HTML bullet points
    if len(formatted_points) > 1:
        html_points = "<ul style='text-align: left; padding-left: 20px;'>"
        for point in formatted_points:
            # Check if point is already formatted (header)
            if point.startswith('<strong>'):
                html_points += f"<li style='margin-bottom: 15px; line-height: 1.6;'>{point}</li>"
            else:
                html_points += f"<li style='margin-bottom: 10px; line-height: 1.6;'>{point}</li>"
        html_points += "</ul>"
        return html_points
    else:
        return text

@app.route('/', methods=['GET', 'POST'])
def home():
    complete_content = ""
    submit_clicked = False
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]

    if request.method == 'POST':
        user_input = request.form['myTextarea'].strip().lower()
        submit_clicked = True

        if user_input in greetings:
            complete_content = "Hello! How can I assist you with your legal questions today?"
        else:
            try:
                client = Groq(
                    api_key=os.getenv('GROQ_API_KEY')
                )

                system_prompt = (
                    "You are a legal expert specializing in Indian law, including the Constitution, statutes, and state-specific laws. "
                    "Answer only law-related questions as if explaining to someone with basic legal knowledge. "
                    "Structure your response with clear sections using headers like 'Definition', 'Punishment', 'Key Provisions', etc. "
                    "Use bullet points (*) for listing items and provide concise, accurate information. "
                    "If a question is not about legal matters, reply with: "
                    "'I apologize, but my expertise lies in legal matters. Would you like to ask a law-related question?' "
                    "Do not provide non-law-related information, even if asked."
                )

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                    top_p=1,
                    stream=True,
                    stop=None,
                )

                raw_content = ""
                for chunk in completion:
                    raw_content += chunk.choices[0].delta.content or ""

                # Format the response into points
                complete_content = format_response_to_points(raw_content)
                
            except Exception as e:
                complete_content = f"Error: {str(e)}. Please check your GROQ_API_KEY environment variable."

        return render_template('home.html', main=complete_content, submit_clicked=submit_clicked)

    return render_template('home.html', main="", submit_clicked=submit_clicked)

if __name__ == '__main__':
    app.run(debug=True)
