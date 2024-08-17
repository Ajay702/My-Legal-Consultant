from flask import Flask, render_template, request
from groq import Groq  
import os

app = Flask(__name__)

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
            print(client)
            system_prompt = (
                "You are a legal expert specializing in Indian law, including the Constitution, statutes, and state-specific laws. "
                "Answer only law-related questions as if i am 5 in law. If a question is not about legal matters, reply with: "
                "'I apologize, but my expertise lies in legal matters. Would you like to ask a law-related question?' "
                "Do not provide non-law-related information, even if asked."
            )

            completion = client.chat.completions.create(
                model="llama3-70b-8192",
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

            for chunk in completion:
                complete_content += chunk.choices[0].delta.content or ""

 
        return render_template('home.html', main=complete_content, submit_clicked=submit_clicked)

    return render_template('home.html', main="", submit_clicked=submit_clicked)

if __name__ == '__main__':
    app.run()
