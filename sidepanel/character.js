import { invokeModel } from "./api.js";

export const extractCharacters = async (paragraph) => {
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

  return invokeModel(payload);
};

export const summarizeCharacterNotes = async (character, actions, wordLimit = 100) => {
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

  return invokeModel(payload);
};

export const updateNotesWithParagraph = async (paragraph, previousNotes = {}, wordLimit = 100) => {
  const extractedText = await extractCharacters(paragraph);

  if (extractedText.toLowerCase().includes("<none>")) {
    console.log("No characters found in the paragraph.");
    return previousNotes;
  }

  const lines = extractedText.split("\n");
  const updatedNotes = { ...previousNotes };

  for (const line of lines) {
    if (line.includes(":")) {
      const [name, action] = line.split(":").map((s) => s.trim());
      if (!Array.isArray(updatedNotes[name])) {
        updatedNotes[name] = [];
      }
      updatedNotes[name].push(action);
    }
  }

  for (const [character, actions] of Object.entries(updatedNotes)) {
    updatedNotes[character] = await summarizeCharacterNotes(character, actions, wordLimit);
  }

  return updatedNotes;
};
