const form = document.getElementById("query-form");
const queryInput = document.getElementById("query");
const responseOutput = document.getElementById("response");
const statusLabel = document.getElementById("status");

function updateStatus(text, isError = false) {
    statusLabel.textContent = text;
    statusLabel.style.backgroundColor = isError ? "#fee2e2" : "#eef2ff";
    statusLabel.style.color = isError ? "#b91c1c" : "#4338ca";
}

async function postQuery(query) {
    const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
    });

    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || response.statusText || "Request failed");
    }

    return response.json();
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = queryInput.value.trim();
    if (!query) {
        updateStatus("Enter a query before submitting.", true);
        return;
    }

    responseOutput.textContent = "Running agent query...";
    updateStatus("Processing...");
    form.querySelector("button").disabled = true;

    try {
        const result = await postQuery(query);
        responseOutput.textContent = result.answer || JSON.stringify(result, null, 2);
        updateStatus("Completed");
    } catch (error) {
        responseOutput.textContent = `Error: ${error.message}`;
        updateStatus("Failed", true);
    } finally {
        form.querySelector("button").disabled = false;
    }
});
