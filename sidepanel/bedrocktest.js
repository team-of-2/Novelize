// Import required AWS SDK components
//import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock";
import {
    BedrockRuntimeClient,
    InvokeModelCommand,
  } from "@aws-sdk/client-bedrock-agent-runtime";
//import Bedrock from '@aws-sdk/client-bedrock';
//const { BedrockRuntimeClient, InvokeModelCommand } = Bedrock;
// Initialize Bedrock Runtime Client
const client = new BedrockRuntimeClient({ region: "us-east-1" }); // Replace with your region

/**
 * Function to interact with Amazon Bedrock
 * @param {string} prompt - The prompt to send to the Bedrock model.
 * @returns {Promise<string>} - The model's response.
 */
async function interactWithBedrock(prompt) {
  const command = new InvokeModelCommand({
    modelId: "anthropic.claude-v2", // Replace with your model ID
    contentType: "application/json",
    body: JSON.stringify({
      prompt,
      max_tokens_to_sample: 200, // Adjust token limit as needed
    }),
  });

  try {
    const response = await client.send(command);
    const result = JSON.parse(new TextDecoder("utf-8").decode(response.body));
    return result.text;
  } catch (error) {
    console.error("Error interacting with Bedrock:", error);
    throw error;
  }
}

// Example usage
(async () => {
  const prompt = "Explain the significance of the AI revolution in simple terms.";
  console.log("Sending prompt to Amazon Bedrock...");
  const response = await interactWithBedrock(prompt);
  console.log("Response from Bedrock:", response);
})();
