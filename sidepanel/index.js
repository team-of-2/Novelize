import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { updateNotesWithParagraph } from "./bedrock-runtime/character.js";
// The underlying model has a context of 1,024 tokens, out of which 26 are used by the internal prompt,
// leaving about 998 tokens for the input text. Each token corresponds, roughly, to about 4 characters, so 4,000
// is used as a limit to warn the user the content might be too long to summarize.
const MAX_MODEL_CHARS = 4000;

let pageContent = '';

const summaryElement = document.body.querySelector('#summary-card-container');
const warningElement = document.body.querySelector('#warning');
const summaryTypeSelect = document.querySelector('#type');
const summaryFormatSelect = document.querySelector('#format');
const summaryLengthSelect = document.querySelector('#length');

function onConfigChange() {
  const oldContent = pageContent;
  pageContent = '';
  onContentChange(oldContent);
}

[summaryTypeSelect, summaryFormatSelect, summaryLengthSelect].forEach((e) =>
  e.addEventListener('change', onConfigChange)
);

chrome.storage.session.get('pageContent', ({ pageContent }) => {
  onContentChange(pageContent);
});

chrome.storage.session.onChanged.addListener((changes) => {
  const pageContent = changes['pageContent'];
  onContentChange(pageContent.newValue);
});

async function onContentChange(newContent) {
  if (pageContent == newContent) {
    // no new content, do nothing
    return;
  }
  pageContent = newContent;
  let summary;
  let notes = {};
  if (newContent) {
    if (newContent.length > MAX_MODEL_CHARS) {
      updateWarning(
        `Text is too long for summarization with ${newContent.length} characters (maximum supported content length is ~4000 characters).`
      );
    } else {
      updateWarning('');
    }
    showSummary('Loading...');
    console.log('summaryTypeSelect.value:', summaryTypeSelect.value);
    if (summaryTypeSelect.value === 'characters') {
        summary = await updateNotesWithParagraph(paragraph, notes, 50);
        console.log("Final Notes:", summary);
    } else {
        summary = await generateSummary(newContent);
    }
  } else {
    summary = "There's nothing to summarize";
  }
  showSummary(summary);
}

async function generateSummary(text) {
  try {
    const session = await createSummarizer(
      {
        type: summaryTypeSelect.value,
        format: summaryFormatSelect.value,
        length: length.value
      },
      (message, progress) => {
        console.log(`${message} (${progress.loaded}/${progress.total})`);
      }
    );
    const summary = await session.summarize(text);
    session.destroy();
    return summary;
  } catch (e) {
    console.log('Summary generation failed');
    console.error(e);
    return 'Error: ' + e.message;
  }
}

async function createSummarizer(config, downloadProgressCallback) {
  if (!window.ai || !window.ai.summarizer) {
    throw new Error('AI Summarization is not supported in this browser');
  }
  console.log('window.ai:', window.ai);
  console.log('window.ai.summarizer:', window.ai?.summarizer);
  const canSummarize = await window.ai.summarizer.capabilities();
  
  console.log('canSummarize:', canSummarize);
  if (canSummarize.available === 'no') {
    throw new Error('AI Summarization is not supported');
  }
  console.log('canSummarize.available =', canSummarize.available);
  const summarizationSession = await self.ai.summarizer.create(
    config,
    downloadProgressCallback
  );
  if (canSummarize.available === 'after-download') {
    console.log('Downloading model...');
    summarizationSession.addEventListener(
      'downloadprogress',
      downloadProgressCallback
    );
    await summarizationSession.ready;
    console.log('Model downloaded');
  }
  return summarizationSession;
}

async function showSummary(dict) {
    summaryElement.innerHTML = '';
    const summaryCard = (name, events) => {
        const id = `collapse-${name.replace(/\s+/g, '-').toLowerCase()}`;
        return `
            <div class="collapsible-button card" data-toggle="${id}">
                <h3 class="collapsible-header">
                    ${name}
                    <span class="icon" id="icon-${id}">➕</span>
                </h3>
                <div id="${id}" class="collapsible-content">
                    <ul>
                        ${events.map((event) => `<li>${event}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    };

    Object.entries(dict).forEach(([name, events]) => {
        summaryElement.innerHTML += summaryCard(name, events);
    });

    // Add click event listeners for collapsible functionality
    document.querySelectorAll('.collapsible-button').forEach((button) => {
        button.addEventListener('click', () => {
            const content = document.getElementById(button.dataset.toggle);
            const icon = document.getElementById(`icon-${button.dataset.toggle}`);
            if (content.style.display === 'block') {
                content.style.display = 'none';
                icon.textContent = '➕';
            } else {
                content.style.display = 'block';
                icon.textContent = '➖';
            }
        });
    });
}

async function updateWarning(warning) {
  warningElement.textContent = warning;
  if (warning) {
    warningElement.removeAttribute('hidden');
  } else {
    warningElement.setAttribute('hidden', '');
  }
}


/* ******************* Novelize Functions ************************* */
async function generateSummaryByClaude(text) {
  try {
    // Step 1: Extract names and context using Claude API
    const extractedData = await interactWithClaudeAPI({
      task: "Extract names and context",
      input: text,
    });

    // Step 2: Send extracted names to Claude for identification
    const characterData = await interactWithClaudeAPI({
      task: "Identify or classify characters",
      input: {
        names: extractedData.names,
        context: extractedData.context,
        existingCharacters: storedCharacters, // Your maintained list of characters
      },
    });

    // Update your stored characters with the result
    updateStoredCharacters(characterData);

    return generateCharacterSummary(characterData);
  } catch (e) {
    console.log('Summary generation failed');
    console.error(e);
    return 'Error: ' + e.message;
  }
}

async function interactWithClaudeAPI(payload) {
  const response = await fetch('<Claude_API_endpoint>', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer <Your_API_Key>',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Claude API error: ${response.statusText}`);
  }

  return response.json();
}

function updateStoredCharacters(newData) {
  newData.forEach((character) => {
    const existing = storedCharacters.find((c) => c.name === character.name);
    if (existing) {
      existing.actions.push(...character.actions);
    } else {
      storedCharacters.push(character);
    }
  });
}

function generateCharacterSummary(characterData) {
  return characterData
    .map(
      (character) =>
        `**${character.name}**: ${character.actions.join('; ')}`
    )
    .join('\n\n');
}