document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('queryForm');
    const groupInput = document.getElementById('groupNumber');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const loadingDiv = document.getElementById('loading');
    const reportNameBox = document.getElementById('report-name-box');
    const downloadButton = document.getElementById('downloadButton');
    const downloadGroupInput = document.getElementById('downloadGroup');

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const groupValue = groupInput.value;

        // Clear previous results and errors
        resultsDiv.innerHTML = '';
        errorDiv.innerHTML = '';
        loadingDiv.innerHTML = 'Loading...';
        reportNameBox.innerHTML = '';
        downloadButton.style.display = 'none'; // Hide button on new query

        fetch('query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group: groupValue })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Network response was not ok'); });
            }
            return response.json();
        })
        .then(data => {
            loadingDiv.innerHTML = '';
            if (data.error) {
                errorDiv.innerHTML = `Error: ${data.error}`;
            } else if (data.length === 0) {
                resultsDiv.innerHTML = 'No results found.';
            } else {
                reportNameBox.innerHTML = `<h2>Inventory Counting Results</h2>`;
                resultsDiv.innerHTML = createTable(data);
                downloadGroupInput.value = groupValue; // Set the group value for the download form
                downloadButton.style.display = 'inline-block'; // Show button
            }
        })
        .catch(error => {
            loadingDiv.innerHTML = '';
            errorDiv.innerHTML = `Fetch Error: ${error.message}`;
        });
    });

    function createTable(data) {
        const headers = Object.keys(data[0]);
        let table = '<table><thead><tr>';
        headers.forEach(header => table += `<th>${header}</th>`);
        table += '</tr></thead><tbody>';
        data.forEach(row => {
            table += '<tr>';
            headers.forEach(header => table += `<td>${row[header]}</td>`);
            table += '</tr>';
        });
        table += '</tbody></table>';
        return table;
    }
});