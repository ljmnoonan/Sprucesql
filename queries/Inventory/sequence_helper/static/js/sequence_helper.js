document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('queryForm');
    const itemInput = document.getElementById('item');
    const rangeInput = document.getElementById('range');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const loadingDiv = document.getElementById('loading');
    const reportNameBox = document.getElementById('report-name-box');

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const itemValue = itemInput.value;
        const rangeValue = parseInt(rangeInput.value, 10);

        // Clear previous results and errors
        resultsDiv.innerHTML = '';
        errorDiv.innerHTML = '';
        loadingDiv.innerHTML = 'Loading...';
        reportNameBox.innerHTML = '';

        // The API endpoint is at the '/query' path relative to the blueprint's URL prefix
        fetch('query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ item: itemValue, range: rangeValue }) 
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
                reportNameBox.innerHTML = `<h2>Sequence Helper Results</h2>`;
                resultsDiv.innerHTML = createTable(data, itemValue, rangeValue);
            }
        })
        .catch(error => {
            loadingDiv.innerHTML = '';
            errorDiv.innerHTML = `Fetch Error: ${error.message}`;
            console.error('There has been a problem with your fetch operation:', error);
        });
    });

    function createTable(data, targetItem, range) {
        if (!data || data.length === 0) {
            return '<p>Target item not found or has no sequence number.</p>';
        }

        // Find the target item's sequence number from the fetched data.
        const targetRow = data.find(row => row.Item === targetItem);
        if (!targetRow) {
            return '<p>Target item not found in the returned sequence range.</p>';
        }
        const targetSequence = parseInt(targetRow.ReportSequence, 10);
        if (isNaN(targetSequence)) {
            return '<p>The target item does not have a valid sequence number.</p>';
        }

        // Create a map for quick lookups of sequence numbers to items.
        const sequenceMap = new Map(data.map(row => [parseInt(row.ReportSequence, 10), row.Item]));

        // Define the full range of sequence numbers to display.
        const startSequence = targetSequence - range;
        const endSequence = targetSequence + range;

        const headers = ['ReportSequence', 'Item'];
        let table = '<table>';

        // Create table headers
        table += '<thead><tr>';
        table += `<th>${headers[0]}</th><th>${headers[1]}</th>`;
        table += '</tr></thead>';

        // Create table rows
        table += '<tbody>';
        for (let i = startSequence; i <= endSequence; i++) {
            const currentItem = sequenceMap.get(i) || '';
            const isTarget = currentItem === targetItem;
            const rowClass = isTarget ? ' class="target-item-row"' : '';

            table += `<tr${rowClass}>`;
            table += `<td>${i}</td>`;
            table += `<td>${currentItem}</td>`;
            table += '</tr>';
        }
        table += '</tbody></table>';

        return table;
    }
});