import time
import pandas as pd

# Model initialization (assuming the `model.predict` method is synchronous)
from langchain.chains import ConversationChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
import boto3

# Setup Bedrock (modify as per your setup)
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)

# Load the Bedrock model
def load_llm():
    llm = Bedrock(client=bedrock_runtime, model_id="ai21.j2-mid")
    llm.model_kwargs = {
        "maxTokens": 5147,
        "temperature": 0.9,
        "stopSequences": [],
    }
    #llm.model_kwargs = {"temperature": 0.7, "max_tokens_to_sample": 2048}
    model = ConversationChain(llm=llm, verbose=True, memory=ConversationBufferMemory())
    return model

model = load_llm()

# Function to extract a single character and their action
def extract_single_character(text, already_extracted=[]):
    exclude_list = ", ".join(already_extracted) if already_extracted else "None"
    prompt = (
        f"Extract one character and what they did from the following text. "
        f"Avoid characters already extracted: [{exclude_list}]. "
        f"Use the format 'Name: Action'. For example, 'Alice: Went to the market'. "
        f"If no more characters are found, respond with '<end>'.\n\n"
        f"Text:\n{text}"
    )
    result = model.predict(input=prompt)
    time.sleep(1)  # Wait briefly for response
    return result.strip()

# Save character summaries to CSV
def save_to_csv(data, file_name="characters_summary.csv"):
    # Combine actions for each character
    combined_data = {}
    for entry in data:
        character = entry["Character"]
        action = entry["Summary"]
        if character in combined_data:
            combined_data[character] += f"\n{action}"  # Append action as a new line
        else:
            combined_data[character] = action

    # Prepare the combined data for saving
    formatted_data = [{"Character": character, "Summary": actions} for character, actions in combined_data.items()]
    
    # Save to CSV
    df = pd.DataFrame(formatted_data)
    df.to_csv(file_name, index=False)
    print(f"Data saved to {file_name}")

# Main function to process a single passage
def process_text(input_text):
    characters = []  # List to store extracted characters and actions
    already_extracted = []  # Keep track of characters already extracted
    while True:
        response = extract_single_character(input_text, already_extracted)
        
        if "<end>" in response.lower():
            break  # End processing when no more characters are found
        
        if ":" in response:  # Ensure the response is formatted correctly
            name, action = map(str.strip, response.split(":", 1))
            characters.append({"Character": name, "Summary": action})
            already_extracted.append(name)  # Mark this character as processed
        else:
            print(f"Unexpected response format: {response}")
            break  # Exit if the response format is invalid

    save_to_csv(characters)

# Example usage
if __name__ == "__main__":
    input_text = """Alice went to the market and bought some apples. 
    Bob helped her carry the basket. Later, Alice thanked Bob for his help."""
    process_text(input_text)
