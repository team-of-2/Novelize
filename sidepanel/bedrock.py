import boto3
import json
import time
import pandas as pd

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
    print(result)
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
        f"List each character and their actions in the format 'Name: Action'. "
        f"Separate multiple actions for the same character with semicolons. "
        f"If no characters are found, respond with '<none>'.\n\n"
        f"Text:\n{text}"
    )
    result = call_claude_sonet_with_backoff(prompt)
    if result:
        return result.strip()
    else:
        return "<error>"

def process_text_in_one_call(input_text):
    """
    Process a single passage to extract all characters and their actions in one API call.
    """
    result = extract_all_characters(input_text)

    if result.lower() in ["<none>", "<error>"]:
        print("No characters found or an error occurred.")
        return {}

    # Parse the result into a dictionary
    characters = {}
    for line in result.split("\n"):
        if ":" in line:  # Ensure the format 'Name: Action'
            name, actions = map(str.strip, line.split(":", 1))
            if name in characters:
                characters[name] += f"; {actions}"  # Append actions for existing characters
            else:
                characters[name] = actions  # Add new character

    return characters

def process_continued_paragraphs(paragraphs):
    """
    Process multiple paragraphs sequentially, combining character actions across paragraphs.
    """
    all_characters = {}

    for i, paragraph in enumerate(paragraphs):
        print(f"\nProcessing Paragraph {i + 1}...")
        paragraph_characters = process_text_in_one_call(paragraph)

        # Merge results into the main dictionary
        for name, actions in paragraph_characters.items():
            if name in all_characters:
                all_characters[name] += f"; {actions}"  # Append new actions
            else:
                all_characters[name] = actions  # Add new character

    return all_characters

def save_to_csv(characters, file_name="characters_summary.csv"):
    """
    Save character summaries to a CSV file.
    """
    formatted_data = [{"Character": char, "Summary": summary} for char, summary in characters.items()]
    df = pd.DataFrame(formatted_data)
    df.to_csv(file_name, index=False)
    print(f"Data saved to {file_name}")


if __name__ == "__main__":
    # Sample Paragraphs
    paragraphs = [
        """Alice went to the market and bought some apples. 
        Bob helped her carry the basket. Later, Alice thanked Bob for his help.""",
        """Alice returned home with the apples and started baking a pie. 
        Bob joined her and helped peel the apples. Meanwhile, Charlie, their neighbor, came over to borrow some flour. 
        Alice happily shared some flour with Charlie. Later, Bob invited Charlie to stay for dinner, and the three of them enjoyed a meal together.""",
        """The next day, Alice and Bob decided to visit the park. 
        Charlie met them there and brought his dog along. Bob played fetch with Charlie's dog, and Alice took some photos."""
    ]

    # Process all paragraphs
    characters = process_continued_paragraphs(paragraphs)

    # Output the results
    print("\nFinal Character Summaries Across All Paragraphs:")
    for character, summary in characters.items():
        print(f"{character}: {summary}")

    # Save the results to a CSV file
    save_to_csv(characters)
