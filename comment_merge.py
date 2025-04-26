import subprocess
import sys
import re
import time
import tempfile
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from Twitter_post_checker import GroqAPI

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")



def create_temp_script(content, file_name):
    """Create a temporary script file with the given content."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file_name)

    with open(file_path, 'w') as f:
        f.write(content)

    return file_path


def extract_analysis_from_output(output):
    """Extract the factual analysis from the checker script output."""
    # Look for text between "Factual Analysis:" and a line of equal signs
    analysis_match = re.search(r'Factual Analysis:\n={1,80}\n(.*?)={1,80}', output, re.DOTALL)

    if analysis_match:
        # Return the captured group (the analysis)
        return analysis_match.group(1).strip()
    else:
        # Fallback: try to find any analysis-like content
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "analyzing tweet truthfulness" in line.lower():
                # Return the next non-empty line
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith("="):
                        return lines[j].strip()

    return "Based on fact-checking, this tweet's accuracy could not be fully verified."


def is_tweet_false(analysis):
    """Determine if the tweet is false based on the analysis."""
    if not analysis:
        return False
    lower_analysis = analysis.lower()
    # Explicit TRUE detection
    if "this tweet is true" in lower_analysis or "the tweet is true" in lower_analysis:
        return False
    
    # Rest of your existing false detection logic
    false_indicators = [
        "false", "misleading", "incorrect", "untrue", "inaccurate", 
        "no credible", "no evidence", "cannot be verified"
    ]
    
    # Check if any false indicators are in the analysis
    for indicator in false_indicators:
        if indicator in lower_analysis:
            return True
    return any(indicator in lower_analysis for indicator in false_indicators)    
            
    # # If no clear indicators, check if it generally seems negative
    # negative_score = 0
    # positive_score = 0
    
    # # Keywords that might indicate falsehood
    # if any(word in lower_analysis for word in ["doubt", "skeptic", "question", "exaggerat"]):
    #     negative_score += 1
        
    # # Keywords that might indicate truth
    # if any(word in lower_analysis for word in ["confirm", "verify", "true", "accurate", "correct"]):
    #     positive_score += 1
        
    # return negative_score > positive_score


def run_checker_script(tweet_url):
    """Run the Twitter post checker script and capture its output."""
    print(f"Checking factual accuracy of: {tweet_url}")

    # Create a modified version of the checker script that prints the analysis to stdout
    with open("Twitter_post_checker.py", "r") as f:
        checker_content = f.read()

    # Modify the script to accept command line argument
    modified_content = checker_content.replace(
        'tweet_url = input("Enter the Twitter/X post URL (e.g., https://x.com/username/status/123456): ")',
        f'tweet_url = "{tweet_url}"'
    )

    # Create temporary modified script
    temp_checker_path = create_temp_script(modified_content, "temp_checker.py")

    try:
        # Run the modified script
        result = subprocess.run(
            [sys.executable, temp_checker_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("Error running Twitter post checker:")
            print(result.stderr)
            return None

        # Extract the analysis from the output
        return extract_analysis_from_output(result.stdout)

    except Exception as e:
        print(f"Error running checker script: {str(e)}")
        return None
    finally:
        # Clean up
        try:
            os.remove(temp_checker_path)
        except:
            pass


def run_reply_script(post_url, reply_text):
    """Run the Twitter reply script with the given reply text."""
    print(f"Posting reply to: {post_url}")
    print(f"Reply text: {reply_text}")
    
    # Create a modified version of the reply script
    with open("reply_twitter.py", "r") as f:
        reply_content = f.read()

     # Read the selected response if it exists
    try:
         with open("temp_reply.txt", "r") as f:
             selected_response = f.read().strip()
    except:
         selected_response = reply_text  


      
    # Modify the script to use our post URL
    modified_content = reply_content.replace(
        'post_url = "https://x.com/VHindus71/status/1914014956208677189"',
        f'post_url = "{post_url}"'
    )

    # Replace the reply_text with our analysis
    modified_content = modified_content.replace(
       'reply_text = "this is my first reply"',
        f'reply_text = """{selected_response}"""'
     )

    # Create temporary modified script
    temp_reply_path = create_temp_script(modified_content, "temp_reply.py")

    try:
        # Run the modified script
        print("Running Twitter reply script...")
        subprocess.run([sys.executable, temp_reply_path])

    except Exception as e:
        print(f"Error running reply script: {str(e)}")
    finally:
        # Clean up
        try:
            os.remove(temp_reply_path)
            os.remove("temp_reply.txt")
        except:
            pass


def format_reply_text(analysis):
    """Format the analysis to fit Twitter character limits and style."""
    # Twitter has a 280 character limit
    if len(analysis) <= 270:
        return analysis

    # Truncate and add ellipsis
    return analysis[:267] + "..."


def generate_false_response(response_type, analysis, tweet_text):
    """Generate a response for false tweets based on the selected option."""
    # Extract key points from the analysis
    key_points = []
    sentences = re.split(r'[.!?]', analysis)
    for sentence in sentences:
        if any(word in sentence.lower() for word in ["false", "incorrect", "untrue", "no evidence"]):
            key_points.append(sentence.strip())
    
    # If no key points found, use the first sentence
    if not key_points and sentences:
        key_points.append(sentences[0].strip())
    
    # Default key point if none found
    if not key_points:
        key_points.append("This tweet contains false information")
    
    key_point = key_points[0]
    
    # Generate response based on the selected type
    if response_type == "simple":
        return f"Fact check: {key_point}."
    
    elif response_type == "medium":
        jokes = [
            f"Nice try, but nope! {key_point}. Maybe check your sources next time?",
            f"Well, that's what I call creative fiction! {key_point}.",
            f"In today's episode of 'Things That Never Happened'... {key_point}.",
            f"I checked the facts so you don't have to: {key_point}. Better luck next time!"
        ]
        return jokes[hash(tweet_text) % len(jokes)]
    
    elif response_type == "extreme":
        sarcastic = [
            f"Congratulations! This might be the most ridiculous thing I've read today. FACT: {key_point}.",
            f"Wow, did you get your 'facts' from a cereal box? {key_point}. Do better.",
            f"*Spits coffee* SERIOUSLY?! {key_point}. Maybe try journalism school before posting.",
            f"I'm dying of laughter! {key_point}. Please don't quit your day job to become a reporter."
        ]
        return sarcastic[hash(tweet_text) % len(sarcastic)]
    
    # Fallback
    return f"Fact check: {key_point}."


def generate_true_response(analysis):
    """Generate a positive response for true tweets."""
    templates = [
        "Fact check: This appears to be accurate based on available information.",
        "This tweet checks out. The information appears to be factually correct.",
        "Our fact check confirms the accuracy of this information.",
        "The claims in this tweet are supported by credible sources."
    ]
    
    # Choose a template semi-randomly based on the content
    template = templates[hash(analysis) % len(templates)]
    
    # Extract key supporting evidence if available
    evidence = ""
    sentences = re.split(r'[.!?]', analysis)
    for sentence in sentences:
        if any(word in sentence.lower() for word in ["confirm", "support", "evidence", "verify"]):
            evidence = sentence.strip()
            break
    
    if evidence:
        return f"{template} {evidence}."
    else:
        return template


def show_response_options(root, tweet_url, analysis, tweet_text):
    """Show clickable options for false tweet responses."""
    root.title("Response Options")
    
    # Create a frame for the text
    text_frame = ttk.Frame(root, padding="10")
    text_frame.pack(fill="both", expand=True)
    
    # Add the analysis
    ttk.Label(text_frame, text="Analysis Result:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))
    ttk.Label(text_frame, text=analysis, wraplength=500).pack(fill="x", pady=(0, 15))
    
    ttk.Label(text_frame, text="This tweet appears to be FALSE.", 
              font=("Arial", 12, "bold"), foreground="red").pack(pady=(0, 15))
    
    ttk.Label(text_frame, text="Choose a response style:", 
              font=("Arial", 11)).pack(anchor="w", pady=(0, 10))
    
    # Create a frame for the buttons
    button_frame = ttk.Frame(root, padding="10")
    button_frame.pack(fill="x", pady=10)
    
    # Add styled buttons with appropriate callbacks
    style = ttk.Style()
    style.configure("Simple.TButton", background="#e0e0e0")
    style.configure("Medium.TButton", background="#ffd700")
    style.configure("Extreme.TButton", background="#ff6347")
    
    def on_option_selected(option):
        response = generate_false_response(option, analysis, tweet_text)

###
        with open("selected_response.txt", "w") as f:
            f.write(response)
#####


        show_final_confirmation(root, tweet_url, response)
    
    simple_btn = ttk.Button(button_frame, text="Simple Response", style="Simple.TButton",
                          command=lambda: on_option_selected("simple"))
    simple_btn.pack(side="left", padx=10, expand=True, fill="x")
    
    medium_btn = ttk.Button(button_frame, text="Joking Response", style="Medium.TButton",
                          command=lambda: on_option_selected("medium"))
    medium_btn.pack(side="left", padx=10, expand=True, fill="x")
    
    extreme_btn = ttk.Button(button_frame, text="Sarcastic Response", style="Extreme.TButton",
                           command=lambda: on_option_selected("extreme"))
    extreme_btn.pack(side="left", padx=10, expand=True, fill="x")
    
    root.geometry("600x400")
    root.mainloop()


def show_final_confirmation(root, tweet_url, reply_text):
    """Show final confirmation dialog before posting."""
    for widget in root.winfo_children():
        widget.destroy()
    
    root.title("Confirm Reply")
    
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill="both", expand=True)
    
    ttk.Label(frame, text="Ready to post this reply:", 
              font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))
    
    text_area = tk.Text(frame, wrap="word", height=6, width=60)
    text_area.insert("1.0", reply_text)
    text_area.config(state="disabled")
    text_area.pack(fill="both", expand=True, pady=10)
    
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", pady=20)
    
    # Save the reply text immediately to both files
    with open("temp_reply.txt", "w") as f:
        f.write(reply_text)
    
    with open("selected_response.txt", "w") as f:
        f.write(reply_text)
    
    # For true tweets, add an auto-proceed option
    if "appears to be accurate" in reply_text or "checks out" in reply_text or "confirms the accuracy" in reply_text:
        ttk.Label(frame, text="Automatically proceeding in 3 seconds...", 
                  font=("Arial", 10, "italic")).pack(pady=(5, 0))
        
        # Schedule auto-posting with delay
        root.after(3000, lambda: run_twitter_reply_directly(root, tweet_url, reply_text))
    
    ttk.Button(btn_frame, text="Post Reply Now", 
               command=lambda: run_twitter_reply_directly(root, tweet_url, reply_text)).pack(side="right", padx=5)
    
    ttk.Button(btn_frame, text="Cancel", 
               command=root.destroy).pack(side="right", padx=5)

def run_twitter_reply_directly(root, tweet_url, reply_text):
    """Directly run the Twitter reply script without closing the window first."""
    # Save the files again just to be safe
    with open("temp_reply.txt", "w") as f:
        f.write(reply_text)
    
    with open("selected_response.txt", "w") as f:
        f.write(reply_text)
    
    print(f"Posting reply: {reply_text}")
    print(f"To tweet: {tweet_url}")
    
    # Run the reply script directly
    try:
        # Create a modified version of the reply script that won't need input at the end
        with open("reply_twitter.py", "r") as f:
            reply_content = f.read()
        
        # Remove the input at the end that waits for user interaction
        modified_content = reply_content.replace(
            'input("Press Enter to close browser...")',
            'time.sleep(60)'  # Let the browser stay open for a minute
        )
        
        # Use our URL and response
        modified_content = modified_content.replace(
            'post_url = "https://x.com/rajlokkhi123/status/1915318877107474904"',
            f'post_url = "{tweet_url}"'
        )
        
        # Create temporary file with modifications
        import tempfile
        import os
        temp_dir = tempfile.gettempdir()
        temp_script_path = os.path.join(temp_dir, "temp_reply_script.py")
        
        with open(temp_script_path, "w") as f:
            f.write(modified_content)
        
        # Run the modified script
        print("Running Twitter reply script directly...")
        import subprocess
        import sys
        subprocess.Popen([sys.executable, temp_script_path])
        
        # Close the UI
        root.destroy()
        
    except Exception as e:
        print(f"Error launching Twitter reply: {str(e)}")
        messagebox.showerror("Error", f"Failed to launch Twitter reply: {str(e)}")


def show_true_response(root, tweet_url, analysis):
    """Show positive response for true tweets with confirmation option."""
    root.title("Tweet analysis result")
    
    # Create a frame for the text
    text_frame = ttk.Frame(root, padding="10")
    text_frame.pack(fill="both", expand=True)
    
    # Add the analysis
    ttk.Label(text_frame, text="Analysis Result:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))
    ttk.Label(text_frame, text=analysis, wraplength=500).pack(fill="x", pady=(0, 15))
    
    ttk.Label(text_frame, text="This tweet appears to be True.", 
              font=("Arial", 12, "bold"), foreground="red").pack(pady=(0, 15))
    
    ttk.Label(text_frame, text="Choose a response style:", 
              font=("Arial", 11)).pack(anchor="w", pady=(0, 10))
    
    # Create a frame for the buttons
    button_frame = ttk.Frame(root, padding="10")
    button_frame.pack(fill="x", pady=10)
    
    # Add styled buttons with appropriate callbacks
    style = ttk.Style()
    style.configure("Simple.TButton", background="#e0e0e0")
    style.configure("Medium.TButton", background="#ffd700")
    style.configure("Extreme.TButton", background="#ff6347")
    
    # Generate the response first
    response = generate_true_response(analysis)

    ####my short response using llm 
    # If response is too long, generate a shorter version
    if len(response) > 250:
        print("Response too long, generating concise version...")
        concise_prompt = f"""
        Please summarize this fact-check response to be under 250 characters for Twitter,
        while preserving the key factual information:
        
        Original response: {response}
        
        Concise version:
        """
        
        # Initialize LLM (you'll need to pass your LLM instance or initialize here)
        llm = GroqAPI(model_id="llama3-8b-8192", api_key=GROQ_API_KEY)
        concise_response = llm.generate(concise_prompt, temperature=0.1, max_tokens=100)
        
        # Fallback if LLM fails or response is still too long
        if len(concise_response) > 250 or not concise_response.strip():
            print("Using fallback shortening method")
            concise_response = response[:225] + "..." if len(response) > 225 else response
        else:
            response = concise_response.strip()


         ###end   
    
    # Save the response immediately to ensure it's available
    with open("selected_response.txt", "w") as f:
        f.write(response)
    


    show_final_confirmation(root, tweet_url, response)
    
    
    
    root.geometry("600x400")
    root.mainloop()

def extract_tweet_text(tweet_url):
    """More robust tweet extraction with proper Chrome setup"""
    try:
        # Create extraction script with proper Chrome setup
        extract_code = f"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_tweet_text(driver, url):
    driver.get(url)
    try:
        tweet_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetText"]'))
        )
        return tweet_element.text
    except Exception as e:
        print(f"Extraction error: {{str(e)}}")
        return None

driver = None
try:
    driver = setup_driver()
    tweet_text = get_tweet_text(driver, '{tweet_url}')
    with open("tweet_text_temp.txt", "w") as f:
        f.write(tweet_text if tweet_text else "")
except Exception as e:
    print(f"Error during extraction: {{str(e)}}")
finally:
    if driver:
        driver.quit()
"""

        # Create temporary script
        temp_extractor_path = create_temp_script(extract_code, "temp_tweet_extractor.py")
        
        # Run the script with timeout
        subprocess.run(
            [sys.executable, temp_extractor_path],
            check=True,
            timeout=30  # 30 second timeout
        )
        
        # Read results
        try:
            with open("tweet_text_temp.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""
            
    except subprocess.TimeoutExpired:
        print("Tweet extraction timed out")
        return ""
    except Exception as e:
        print(f"Error extracting tweet text: {{str(e)}}")
        return ""
    finally:
        # Clean up
        try:
            os.remove(temp_extractor_path)
            os.remove("tweet_text_temp.txt")
        except:
            pass

def main():
    # Get tweet URL from command line or prompt
    if len(sys.argv) > 1:
        tweet_url = sys.argv[1]
    else:
        tweet_url = input("Enter the Twitter/X post URL to analyze and reply to: ")
    
    # Create GUI root
    root = tk.Tk()
    root.withdraw()  # Hide the main window initially
    
    # Step 1: Run the checker script to analyze the tweet
    analysis = run_checker_script(tweet_url)
    
    if not analysis:
        messagebox.showerror("Error", "Failed to generate analysis. Please try again.")
        return
    
    print("\nGenerated analysis:")
    print("-" * 60)
    print(analysis)
    print("-" * 60)
    
    # Extract tweet text for context in responses
    tweet_text = extract_tweet_text(tweet_url)
    
    # Check if the tweet is false
    is_false = is_tweet_false(analysis)
    
    
    # Show appropriate UI based on analysis
    root.deiconify()  # Show the window
    
    if is_false:
        # Show options for false tweet
        show_response_options(root, tweet_url, analysis, tweet_text)
    else:
        # Show positive response for true tweet
        show_true_response(root, tweet_url, analysis)


if __name__ == "__main__":
    main()