from flask import Flask, render_template, request
from groq import Groq  
import os
import re

app = Flask(__name__)

def format_response_to_points(text):
    """Convert paragraph text to bullet points"""
    if not text.strip():
        return text
    
    # Split by sentences and clean up
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    formatted_points = []
    
    current_point = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if this sentence starts a new topic/section
        if (sentence.startswith(('Section ', 'The ', 'Some notable', 'Additionally', 'It\'s worth noting')) or 
            re.match(r'^\d+\.', sentence) or
            len(current_point) > 200):  # If current point is getting too long
            
            if current_point:
                formatted_points.append(current_point.strip())
            current_point = sentence
        else:
            current_point += " " + sentence
    
    # Add the last point
    if current_point:
        formatted_points.append(current_point.strip())
    
    # Format as HTML bullet points
    if len(formatted_points) > 1:
        html_points = "<ul style='text-align: left; padding-left: 20px;'>"
        for point in formatted_points:
            html_points += f"<li style='margin-bottom: 10px; line-height: 1.6;'>{point}</li>"
        html_points += "</ul>"
        return html_points
    else:
        return text  # Return original if couldn't split meaningfully

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
            client = Groq(
                api_key=os.getenv('GROQ_API_KEY')
            )
            
            system_prompt = (
                "You are a legal expert specializing in Indian law, including the Constitution, statutes, and state-specific laws. "
                "Answer only law-related questions as if i am 5 in law. Structure your response with clear sections and points for better readability. "
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
                temperature=1,
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
 
        return render_template('home.html', main=complete_content, submit_clicked=submit_clicked)
    
    return render_template('home.html', main="", submit_clicked=submit_clicked)

if __name__ == '__main__':
    app.run()
