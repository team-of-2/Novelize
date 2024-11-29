import { updateNotesWithParagraph } from "./character.js";
import { showSummary, updateWarning } from "./ui.js";

const MAX_MODEL_CHARS = 4000;
let notes = {};

document.getElementById("analyze-button").addEventListener("click", async () => {
  const paragraph = document.getElementById("input-text").value;

  if (paragraph.length > MAX_MODEL_CHARS) {
    updateWarning(`Text is too long (${paragraph.length} characters).`);
    return;
  }

  updateWarning("");
  showSummary({ Loading: ["Analyzing paragraph..."] });

  try {
    notes = await updateNotesWithParagraph(paragraph, notes);
    showSummary(notes);
  } catch (error) {
    console.error("Error updating notes:", error);
    updateWarning("Failed to process the text. Check the console for details.");
  }
});
