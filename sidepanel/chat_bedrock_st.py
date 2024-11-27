import time
import pandas as pd
from langchain_aws import ChatBedrock
import boto3

# Setup Bedrock Client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)

# Function to load the Bedrock model
def load_llm():
    llm = ChatBedrock(
        client=bedrock_runtime,
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",  # Replace with your model ID
        model_kwargs={
            "temperature": 0.7,
            "max_tokens": 2048,
        },
    )
    return llm


# Initialize the model
model = load_llm()

import time

def invoke_with_retry_and_rate_limit(messages, max_retries=5, backoff_factor=2, rate_limit=30):
    retry_count = 0
    while retry_count < max_retries:
        try:
            time.sleep(rate_limit)  # Apply rate-limiting
            result = model.invoke(input=messages)
            return result.content.strip()
        except Exception as e:
            if "ThrottlingException" in str(e):
                wait_time = backoff_factor ** retry_count
                print(f"ThrottlingException: Retrying in {60} seconds...")
                time.sleep(wait_time)
                retry_count += 1
            else:
                print(f"Error during model invocation: {e}")
                return "<error>"
    print("Max retries reached. Exiting.")
    return "<error>"

def extract_single_character(text, already_extracted=[]):
    exclude_list = ", ".join(already_extracted) if already_extracted else "None"
    prompt = (
        f"Extract one character and what they did from the following text. "
        f"Avoid characters already extracted: [{exclude_list}]. "
        f"Use the format 'Name: Action'. For example, 'Alice: Went to the market'. "
        f"If all characters from the text are already extracted, respond with '<end>', exactly with the <> brackets.\n\n"
        f"Text:\n{text}"
    )
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]
    return invoke_with_retry_and_rate_limit(messages)



# Function to save character summaries to a CSV file
def save_to_csv(data, file_name="characters_summary.csv"):
    # Combine actions for each character
    combined_data = {}
    for character, actions in data.items():
        if character in combined_data:
            combined_data[character] += f"\n{actions}"  # Append action as a new line
        else:
            combined_data[character] = actions

    # Prepare data for saving
    formatted_data = [{"Character": character, "Summary": actions} for character, actions in combined_data.items()]
    df = pd.DataFrame(formatted_data)
    df.to_csv(file_name, index=False)
    print(f"Data saved to {file_name}")

# Main function to process a single passage
def process_text(input_text, characters=None):
    # Initialize characters dictionary if not provided
    if characters is None:
        characters = {}

    already_extracted = list(characters.keys())  # Start with characters already known
    while True:
        response = extract_single_character(input_text, already_extracted)

        if response.lower() in ["<end>", "<error>"]:
            break  # End processing if no more characters are found or on error

        if ":" in response:  # Ensure the response is formatted correctly
            name, action = map(str.strip, response.split(":", 1))

            # Update character summaries
            if name in characters:
                characters[name] += f"\n{action}"  # Append the new action
            else:
                characters[name] = action  # Add new character with their action

            already_extracted.append(name)  # Mark this character as processed
        else:
            print(f"Unexpected response format: {response}")
            break  # Exit if the response format is invalid

    return characters  # Return updated characters

# Example usage
if __name__ == "__main__":
    # Paragraph 1
    input_text_1 = """Alice went to the market and bought some apples. 
    Bob helped her carry the basket. Later, Alice thanked Bob for his help."""
    characters = process_text(input_text_1)

    # Paragraph 2
    input_text_2 = """Alice returned home with the apples and started baking a pie. 
    Bob joined her and helped peel the apples. Meanwhile, Charlie, their neighbor, came over to borrow some flour. 
    Alice happily shared some flour with Charlie. Later, Bob invited Charlie to stay for dinner, and the three of them enjoyed a meal together."""
    #characters = process_text(input_text_2, characters)

    # Save to CSV
    save_to_csv(characters)
