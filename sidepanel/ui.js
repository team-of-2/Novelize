export const showSummary = (notes) => {
    const summaryElement = document.getElementById("summary-card-container");
    summaryElement.innerHTML = "";
  
    Object.entries(notes).forEach(([name, actions]) => {
      const summaryCard = `
        <div>
          <h3>${name}</h3>
          <ul>${actions.map((action) => `<li>${action}</li>`).join("")}</ul>
        </div>
      `;
      summaryElement.innerHTML += summaryCard;
    });
  };
  
  export const updateWarning = (message) => {
    const warningElement = document.getElementById("warning");
    warningElement.textContent = message;
    warningElement.style.display = message ? "block" : "none";
  };
  