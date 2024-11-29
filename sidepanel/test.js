import { updateNotesWithParagraph } from "./bedrock-runtime/character.js"; // Adjust the import path accordingly

(async () => {
  // Initialize with empty notes
  let notes = {};

  // Test paragraphs
  const paragraphs = [
    "Alice went to the market and bought some apples. Bob helped her carry the basket.",
    "Charlie joined Alice and Bob in the park. Alice took some photos while Bob played fetch with Charlie's dog.",
    "Later, Alice and Bob decided to have a picnic. Charlie brought his dog to join them.",
  ];

  // Process each paragraph sequentially
  for (const paragraph of paragraphs) {
    console.log(`Processing paragraph: ${paragraph}`);
    notes = await updateNotesWithParagraph(paragraph, notes, 50); // Word limit set to 50
  }

  // Log the final notes
  console.log("Final Notes:", notes);
})();
