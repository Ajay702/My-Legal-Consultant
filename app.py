from flask import Flask, render_template, request
from groq import Groq  
import os
import re

app = Flask(__name__)

def format_legal_response(text):
    """Format legal response with proper HTML structure"""
    if not text.strip():
        return text
    
    # Clean up the text first
    text = text.strip()
    
    # Split by common section markers and format
    sections = []
    current_section = ""
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a main heading (usually in **bold** or with ===)
        if (line.startswith('**') and line.endswith('**')) or '===' in line:
            if current_section:
                sections.append(('section', current_section))
                current_section = ""
            # Remove markdown formatting
            clean_heading = line.replace('**', '').replace('=', '').strip()
            sections.append(('heading', clean_heading))
            
        # Check if this is a subheading (usually starts with ##)
        elif line.startswith('##') or (line.startswith('**') and not line.endswith('**')):
            if current_section:
                sections.append(('section', current_section))
                current_section = ""
            clean_subheading = line.replace('#', '').replace('**', '').strip()
            sections.append(('subheading', clean_subheading))
            
        # Check if this is a bullet point
        elif line.startswith('* ') or line.startswith('- '):
            point = line[2:].strip()
            sections.append(('bullet', point))
            
        # Regular content
        else:
            if current_section:
                current_section += " " + line
            else:
                current_section = line
    
    # Add any remaining content
    if current_section:
        sections.append(('section', current_section))
    
    # Generate HTML
    html_output = ""
    in_list = False
    
    for section_type, content in sections:
        if section_type == 'heading':
            if in_list:
                html_output += "</ul>"
                in_list = False
            html_output += f'<h2 style="color: #667eea; font-size: 1.4em; margin: 25px 0 15px 0; font-weight: 600; border-bottom: 2px solid #667eea; padding-bottom: 8px;">{content}</h2>'
            
        elif section_type == 'subheading':
            if in_list:
                html_output += "</ul>"
                in_list = False
            html_output += f'<h3 style="color: #667eea; font-size: 1.2em; margin: 20px 0 12px 0; font-weight: 600;">{content}</h3>'
            
        elif section_type == 'bullet':
            if not in_list:
                html_output += '<ul style="margin: 15px 0; padding-left: 25px; list-style-type: disc;">'
                in_list = True
            html_output += f'<li style="margin-bottom: 8px; line-height: 1.7; color: #2c3e50;">{content}</li>'
            
        elif section_type == 'section':
            if in_list:
                html_output += "</ul>"
                in_list = False
            # Split long paragraphs into sentences for better readability
            sentences = re.split(r'(?<=[.!?])\s+', content)
            if len(sentences) > 2:
                html_output += '<ul style="margin: 15px 0; padding-left: 25px; list-style-type: disc;">'
                for sentence in sentences:
                    if sentence.strip():
                        html_output += f'<li style="margin-bottom: 8px; line-height: 1.7; color: #2c3e50;">{sentence.strip()}</li>'
                html_output += '</ul>'
            else:
                html_output += f'<p style="margin: 12px 0; line-height: 1.7; color: #2c3e50;">{content}</p>'
    
    if in_list:
        html_output += "</ul>"
    
    return html_output if html_output else text

@app.route('/', methods=['GET', 'POST'])
def home():
    complete_content = ""
    submit_clicked = False
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    
    if request.method == 'POST':
        user_input = request.form['myTextarea'].strip().lower()
        submit_clicked = True
        
        if user_input in greetings:
            complete_content = """
            <h2 style="color: #667eea; font-size: 1.4em; margin: 25px 0 15px 0; font-weight: 600;">Welcome to Legal Advisor!</h2>
            <p style="margin: 12px 0; line-height: 1.7; color: #2c3e50;">
                Hello! I'm here to assist you with your legal questions related to Indian law. 
                I can help you understand various legal concepts, procedures, and rights under Indian jurisdiction.
            </p>
            <p style="margin: 12px 0; line-height: 1.7; color: #2c3e50;">
                Please feel free to ask me about any legal matter you'd like to understand better.
            </p>
            """
        else:
            client = Groq(
                api_key=os.getenv('GROQ_API_KEY')
            )
            
            system_prompt = (
                "You are a professional legal expert specializing in Indian law. "
                "Structure your responses professionally with clear headings and bullet points. "
                "Use the following format:\n\n"
                "**Main Topic**\n"
                "Brief introduction paragraph.\n\n"
                "**Key Points**\n"
                "* First important point with clear explanation\n"
                "* Second important point with details\n"
                "* Third point if applicable\n\n"
                "**Legal Provisions**\n"
                "* Relevant sections and acts\n"
                "* Specific legal references\n\n"
                "**Important Notes**\n"
                "* Any warnings or disclaimers\n"
                "* Recommendations for legal consultation\n\n"
                "Keep explanations clear and professional. If the question is not law-related, "
                "politely redirect to legal matters only."
            )
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,  # Slightly lower for more consistent formatting
                max_tokens=1024,
                top_p=1,
                stream=True,
                stop=None,
            )
            
            raw_content = ""
            for chunk in completion:
                raw_content += chunk.choices[0].delta.content or ""
            
            # Format the response
            complete_content = format_legal_response(raw_content)
 
        return render_template('home.html', main=complete_content, submit_clicked=submit_clicked)
    
    return render_template('home.html', main="", submit_clicked=submit_clicked)

if __name__ == '__main__':
    app.run(debug=True)
