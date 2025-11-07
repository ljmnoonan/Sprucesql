document.addEventListener('DOMContentLoaded', function() {
    // --- Element References ---
    const form = document.getElementById('queryForm');
    const groupInput = document.getElementById('groupNumber');
    const errorDiv = document.getElementById('error');
    const loadingDiv = document.getElementById('loading');
    const tableHeaderInfo = document.getElementById('table-header-info');
    const downloadButton = document.getElementById('downloadButton');
    const groupDataList = document.getElementById('group-list');
    const groupDataMap = new Map();

    // --- Function to fetch and populate the group datalist on page load ---
    function loadGroupData() {
        fetch('groups') // Fetches from the new /groups endpoint
            .then(response => {
                if (!response.ok) throw new Error('Failed to load group data.');
                return response.json();
            })
            .then(data => {
                data.forEach(group => {
                    const option = document.createElement('option');
                    // The value is what gets submitted, the text is what's displayed.
                    option.value = group.Group;
                    option.textContent = `${group.Group} - ${group.Description}`;
                    groupDataMap.set(group.Group.toString(), group.Description);
                    groupDataList.appendChild(option);
                });
            })
            .catch(error => console.error('Error loading group data:', error));
    }

    // --- Event Listeners ---
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const groupValue = groupInput.value;

        // Clear previous errors
        errorDiv.innerHTML = '';
        loadingDiv.innerHTML = 'Loading...';
        tableHeaderInfo.textContent = '';
        document.title = 'Inventory Count Worksheet'; // Reset title on new query
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
                populateTable([]); // Clear the table
                errorDiv.innerHTML = 'No results found.'; // Display message in error div
            } else {
                const groupNumber = groupValue.split(' - ')[0];
                const groupDescription = groupDataMap.get(groupNumber) || '';
                const titleText = `${groupNumber} - ${groupDescription}`;
                tableHeaderInfo.textContent = titleText;
                document.title = `${titleText} Count Worksheet`;
                populateTable(data);
                downloadButton.style.display = 'inline-block';
            }
        })
        .catch(error => {
            loadingDiv.innerHTML = '';
            errorDiv.innerHTML = `Fetch Error: ${error.message}`;
        });
    });

    downloadButton.addEventListener('click', function() {
        const groupValue = groupInput.value;
        // Construct the URL and trigger the download
        window.location.href = `download_xlsx?group=${encodeURIComponent(groupValue)}`;
    });

    /**
     * Formats a number to have a maximum of 2 decimal places and no trailing zeros.
     * @param {number|string} num The number to format.
     * @returns {string} The formatted number as a string.
     */
    function formatNumber(num) {
        const number = parseFloat(num);
        return isNaN(number) ? '' : number.toLocaleString('en-US', { maximumFractionDigits: 2 });
    }

    function populateTable(data) {
        const tableBody = document.querySelector('#results tbody');
        const templateRow = document.getElementById('template-row');
        const sectionTemplateRow = document.getElementById('template-section-header');
        const groupNumber = document.getElementById('groupNumber').value.split(' - ')[0];

        // Clear previously generated rows, leaving templates in place.
        while (tableBody.children.length > 2) { // Now we have 2 templates
            tableBody.removeChild(tableBody.lastChild);
        }

        let currentSection = null;

        data.forEach(row => {
            // When the section changes, insert a section header row.
            if (row.Section !== currentSection) {
                currentSection = row.Section;
                const sectionHeaderRow = sectionTemplateRow.cloneNode(true);
                sectionHeaderRow.removeAttribute('id');
                sectionHeaderRow.removeAttribute('style');
                const sectionDescription = row.SectionDescription || 'Uncategorized';
                sectionHeaderRow.querySelector('.section-header').textContent = `${groupNumber}/${currentSection} - ${sectionDescription}`;
                tableBody.appendChild(sectionHeaderRow);
            }

            // Create and populate the item data row.
            const newRow = templateRow.cloneNode(true);
            newRow.removeAttribute('id'); // Remove ID to avoid duplicates
            newRow.removeAttribute('style'); // Make the new row visible

            // If the item is disabled, add a class to the row for styling
            if (row.Disabled === true) {
                newRow.classList.add('disabled-item');
            }

            // Populate cells using querySelector for reliability
            newRow.querySelector('[data-col="Item"]').textContent = row.Item;
            newRow.querySelector('[data-col="BaseUnitofMeasure"]').textContent = row.BaseUnitofMeasure;
            newRow.querySelector('[data-col="OnHand"]').textContent = formatNumber(row.OnHand);
            newRow.querySelector('[data-col="Committed"]').textContent = formatNumber(row.Committed);
            newRow.querySelector('[data-col="OnOrder"]').textContent = formatNumber(row.OnOrder);
            newRow.querySelector('[data-col="Description"]').textContent = row.Description;

            tableBody.appendChild(newRow);
        });
    }

    // --- Initial Setup ---
    loadGroupData(); // Load the group data as soon as the page is ready
});