import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

/**
 * Extract all characters and their actions from a paragraph.
 * @param {string} paragraph - The paragraph to analyze.
 * @returns {Promise<object>} - A promise resolving to character notes.
 */
const extractCharacters = async (paragraph) => {
  const prompt = `
Extract all characters and their actions from the following text.
List each character and their actions in the format:
Name: Action
Separate characters with a newline. If no characters are found, respond with "<none>".

Text:
${paragraph}
`;

  const payload = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 1000,
    messages: [
      {
        role: "user",
        content: [{ type: "text", text: prompt }],
      },
    ],
  };

  const command = new InvokeModelCommand({
    contentType: "application/json",
    body: JSON.stringify(payload),
    modelId: "anthropic.claude-3-sonnet-20240229-v1:0", // Replace with your model ID
  });

  try {
    const apiResponse = await client.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(apiResponse.body));
    return responseBody.content[0].text;
  } catch (error) {
    console.error("Error extracting characters:", error);
    throw error;
  }
};

/**
 * Summarize notes for a specific character.
 * @param {string} character - The character's name.
 * @param {string[]} actions - List of actions.
 * @param {number} wordLimit - Maximum word count for the summary.
 * @returns {Promise<string>} - A summarized note for the character.
 */
const summarizeCharacterNotes = async (character, actions, wordLimit = 100) => {
    if (!Array.isArray(actions)) {
      throw new TypeError(`Expected actions to be an array but received: ${typeof actions}`);
    }
  
    const fullText = actions.join("; ");
    const wordCount = fullText.split(" ").length;
  
    if (wordCount <= wordLimit) {
      return fullText;
    }
  
    const prompt = `
  Summarize the following notes about ${character}:
  ${fullText}
  Limit the summary to ${wordLimit} words.
  `;
  
    const payload = {
      anthropic_version: "bedrock-2023-05-31",
      max_tokens: 1000,
      messages: [
        {
          role: "user",
          content: [{ type: "text", text: prompt }],
        },
      ],
    };
  
    const command = new InvokeModelCommand({
      contentType: "application/json",
      body: JSON.stringify(payload),
      modelId: "anthropic.claude-3-sonnet-20240229-v1:0", // Replace with your model ID
    });
  
    try {
      const apiResponse = await client.send(command);
      const responseBody = JSON.parse(new TextDecoder().decode(apiResponse.body));
      return responseBody.content[0].text.trim();
    } catch (error) {
      console.error("Error summarizing character notes:", error);
      return fullText; // Fallback to full notes if summarization fails
    }
  };

/**
 * Updates character notes based on a new paragraph.
 * @param {string} paragraph - The paragraph to analyze.
 * @param {object} previousNotes - Existing character notes.
 * @param {number} wordLimit - Maximum word count for each character's summary.
 * @returns {Promise<object>} - Updated character notes.
 */
export const updateNotesWithParagraph = async (paragraph, previousNotes = {}, wordLimit = 100) => {
    // Extract characters and their actions
    const extractedText = await extractCharacters(paragraph);
  
    if (extractedText.toLowerCase().includes("<none>")) {
      console.log("No characters found in the paragraph.");
      return previousNotes;
    }
  
    // Parse the extracted text and update notes
    const lines = extractedText.split("\n");
    const updatedNotes = { ...previousNotes };
  
    for (const line of lines) {
      if (line.includes(":")) {
        const [name, action] = line.split(":").map((s) => s.trim());
        if (!Array.isArray(updatedNotes[name])) {
          updatedNotes[name] = []; // Ensure notes for each character are initialized as an array
        }
        updatedNotes[name].push(action);
      }
    }
  
    // Summarize notes if they exceed the word limit
    for (const [character, actions] of Object.entries(updatedNotes)) {
      if (!Array.isArray(actions)) {
        console.error(`Expected actions to be an array for character "${character}" but got:`, actions);
        continue; // Skip invalid entries
      }
      updatedNotes[character] = await summarizeCharacterNotes(character, actions, wordLimit);
    }
  
    return updatedNotes;
  };
  