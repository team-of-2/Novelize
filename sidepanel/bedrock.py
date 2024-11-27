import boto3
import json
import time
import pandas as pd

# Global variable for the maximum note word count limit
MAX_CHARACTER_COUNT = 500

# Setup bedrock
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2",
)

def call_claude_sonet(prompt):

    prompt_config = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    body = json.dumps(prompt_config)

    modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
    accept = "application/json"
    contentType = "application/json"

    response = bedrock_runtime.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get("body").read())

    results = response_body.get("content")[0].get("text")
    return results

def call_claude_sonet_with_backoff(prompt, max_retries=5):
    """
    Calls Claude with exponential backoff in case of throttling.
    """
    prompt_config = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    body = json.dumps(prompt_config)
    modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
    accept = "application/json"
    contentType = "application/json"

    retry_count = 0
    backoff_factor = 2  # Exponential backoff multiplier

    while retry_count < max_retries:
        try:
            response = bedrock_runtime.invoke_model(
                body=body, modelId=modelId, accept=accept, contentType=contentType
            )
            response_body = json.loads(response.get("body").read())
            return response_body.get("content")[0].get("text")
        except Exception as e:
            if "Too many requests" in str(e):
                wait_time = backoff_factor ** retry_count + 1
                print(f"Throttling error. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                retry_count += 1
            else:
                print(f"Error during Claude invocation: {e}")
                return None
    print("Max retries reached. Exiting.")
    return None

def extract_single_character(text, already_extracted=[]):
    """
    Extract one character and their action from the text.
    Measure the time taken for the extraction.
    """
    exclude_list = ", ".join(already_extracted) if already_extracted else "None"
    prompt = (
        f"Extract one character and what they did from the following text. "
        f"Avoid characters already extracted: [{exclude_list}]. "
        f"Use the format 'Name: Action'. For example, 'Alice: Went to the market'. "
        f"If all characters from the text are already extracted, respond with '<end>', exactly with the <> brackets.\n\n"
        f"Text:\n{text}"
    )

    start_time = time.time()  # Record the start time
    result = call_claude_sonet_with_backoff(prompt)
    #print(result)
    end_time = time.time()  # Record the end time

    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f"Time taken for single character extraction: {elapsed_time:.2f} seconds")

    if result:
        return result.strip()
    else:
        return "<error>"

def extract_all_characters(text):
    """
    Extract all characters and their actions from the text in one API call.
    """
    prompt = (
        f"Extract all characters and what they did from the following text. "
        f"List each character and their actions in the format 'Name: Action'. For example, 'President Washington: Addressed the nation in his inaugural speech'. "
        f"Separate multiple actions for the same character with semicolons. "
        f"If no characters are found, respond with '<none>'.\n\n"
        f"Text:\n{text}"
    )
    result = call_claude_sonet_with_backoff(prompt)
    if result:
        return result.strip()
    else:
        return "<error>"

def parse_extracted_characters(extracted_text):
    """
    Parse the extracted text to create a list of characters and actions.
    """
    characters = []
    for line in extracted_text.split("\n"):
        if ":" in line:  # Ensure the format 'Name: Action'
            name, action = map(str.strip, line.split(":", 1))
            characters.append({"name": name, "action": action})
    return characters

def classify_character(name, existing_characters, context):
    """
    Classify if the given name matches an existing character or is a new one.
    """
    prompt = (
        f"Here is a list of existing characters: {', '.join(existing_characters)}.\n"
        f"Determine if the name '{name}' matches one of these characters or is a new character. "
        f"Consider the following context: {context}.\n"
        f"Respond with the matching character's name or '<new>' if it is a new character."
    )
    result = call_claude_sonet_with_backoff(prompt)
    if result:
        return result.strip()
    else:
        return "<error>"

def summarize_character_notes(name, previous_notes, new_action):
    """
    Summarize the character's previous notes with the new action.
    """
    prompt = (
        f"Here are the notes for {name}:\n{previous_notes}\n\n"
        f"Add the following new action to these notes and summarize them:\n{new_action}."
    )
    result = call_claude_sonet_with_backoff(prompt)
    if result:
        return result.strip()
    else:
        return "<error>"

def handle_ambiguous_classification(name, possible_matches, notes, new_action):
    """
    Generate summaries for each possible match and return to the user for selection.
    """
    summaries = {}
    for match in possible_matches:
        summary = summarize_character_notes(match, notes.get(match, ""), new_action)
        summaries[match] = summary

    return summaries

def update_character_notes(name, notes, new_summary):
    """
    Update the notes dictionary with the new summary for the given character.
    """
    if name in notes:
        notes[name] = new_summary
    else:
        notes[name] = new_summary
    return notes

def process_paragraph_with_extraction(paragraph, notes):
    """
    Process a paragraph by extracting all characters, classifying them, 
    and updating their notes.
    """
    # Step 1: Extract all characters from the paragraph
    extracted_text = extract_all_characters(paragraph)

    if "<none>" in extracted_text.lower() or "<error>" in extracted_text.lower():
        print("No characters found or an error occurred.")
        return notes

    # Parse the extracted text into a list of characters and actions
    extracted_characters = parse_extracted_characters(extracted_text)

    # Step 2: Classify and handle each character
    for character_info in extracted_characters:
        name = character_info["name"]
        action = character_info["action"]

        # Classify the character: map to existing or identify as new
        classification = classify_character(name, list(notes.keys()), paragraph)

        if classification in notes:
            # Check if the current notes exceed the word limit
            current_notes = notes.get(classification, "")
            if len(current_notes) > MAX_CHARACTER_COUNT:
                # Summarize notes only if the word count exceeds the limit
                new_summary = summarize_character_notes(
                    classification, current_notes, action
                )
                notes = update_character_notes(classification, notes, new_summary)
                print(f"\nUpdated notes for {classification} (summarized due to exceeding word count)")
                print(f"Summary: {new_summary}")
            else:
                # Append the new action without summarizing
                notes[classification] = current_notes + "; " + action
                print(f"\nUpdated notes for {classification} (appended without summarizing)")
                print(f"Notes: {notes[classification]}")
        #elif "<new>" in classification.lower():
        else:
            # New character, add to notes
            notes[name] = action
        # else:
        #     # Ambiguous classification, handle manually
        #     possible_matches = classification.split(", ")
        #     summaries = handle_ambiguous_classification(name, possible_matches, notes, action)
        #     print(f"Ambiguity detected for {name}. Possible matches:")
        #     for match, summary in summaries.items():
        #         print(f"{match}: {summary}")
        #     # Mock user selection for simplicity
        #     user_choice = possible_matches[0]
        #     notes = update_character_notes(user_choice, notes, summaries[user_choice])

    return notes

if __name__ == "__main__":
    # Sample Paragraphs
    paragraphs = [
        """President Washington addressed the nation in his inaugural speech. 
        George Washington emphasized unity. George later went for a walk in the gardens.""",
        """Washington, the first President of the United States, held a meeting with his cabinet. 
        George Washington expressed concerns about foreign relations."""
    ]

    paragraphs = [
        """Alice went to the market and bought some apples. 
        Bob helped her carry the basket. Later, Alice thanked Bob for his help.""",
        """Alice returned home with the apples and started baking a pie. 
        Bob joined her and helped peel the apples. Meanwhile, Charlie, their neighbor, came over to borrow some flour. 
        Alice happily shared some flour with Charlie. Later, Bob invited Charlie to stay for dinner, and the three of them enjoyed a meal together.""",
        """The next day, Alice and Bob decided to visit the park. 
        Charlie met them there and brought his dog along. Bob played fetch with Charlie's dog, and Alice took some photos."""
    ]

    # Notes dictionary to store summaries
    notes = {}

    # Process each paragraph
    for paragraph in paragraphs:
        notes = process_paragraph_with_extraction(paragraph, notes)

    # Output the results
    print("\nFinal Notes:")
    for character, summary in notes.items():
        print(f"{character}: {summary}")
