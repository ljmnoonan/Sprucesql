document.addEventListener('DOMContentLoaded', () => {
    const queryForm = document.getElementById('queryForm');
    if (queryForm) {
        queryForm.addEventListener('submit', handleQuerySubmit);
    }
});

async function handleQuerySubmit(event) {
    event.preventDefault();
    
    const groupNumber = document.getElementById('groupNumber').value;
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const loadingDiv = document.getElementById('loading');

    resultsDiv.innerHTML = '';
    errorDiv.innerHTML = '';
    loadingDiv.innerHTML = 'Loading...';

    try {
        const response = await fetch('query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group: groupNumber })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'An unknown error occurred.');
        }

        const data = await response.json();
        
        if (data.length === 0) {
            resultsDiv.innerHTML = '<p>No results found.</p>';
            return;
        }

        let table = '<table><thead><tr>';
        const headers = Object.keys(data[0]);
        headers.forEach(header => table += `<th>${header}</th>`);
        table += '</tr></thead><tbody>';

        data.forEach(row => {
            table += '<tr>';
            headers.forEach(header => table += `<td>${row[header] === null ? '' : row[header]}</td>`);
            table += '</tr>';
        });

        table += '</tbody></table>';
        resultsDiv.innerHTML = table;
    } catch (error) {
        errorDiv.innerHTML = `Error: ${error.message}`;
    } finally {
        loadingDiv.innerHTML = '';
    }
}