document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const fileList = document.getElementById('fileList');
    const processBtn = document.getElementById('processBtn');
    const results = document.getElementById('results');
    
    let files = [];
    
    // Handle drag and drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = '#007bff';
    });
    
    dropzone.addEventListener('dragleave', () => {
        dropzone.style.borderColor = '#ccc';
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = '#ccc';
        
        const droppedFiles = Array.from(e.dataTransfer.files).filter(file => 
            file.type === 'application/pdf'
        );
        
        handleFiles(droppedFiles);
    });
    
    // Handle file input
    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', (e) => {
        const selectedFiles = Array.from(e.target.files);
        handleFiles(selectedFiles);
    });
    
    function handleFiles(newFiles) {
        files = [...files, ...newFiles];
        updateFileList();
        processBtn.disabled = files.length === 0;
    }
    
    function updateFileList() {
        fileList.innerHTML = '';
        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <span>${file.name}</span>
                <button onclick="removeFile(${index})">Remove</button>
            `;
            fileList.appendChild(fileItem);
        });
    }
    
    window.removeFile = (index) => {
        files.splice(index, 1);
        updateFileList();
        processBtn.disabled = files.length === 0;
    };
    
    // Handle form submission
    processBtn.addEventListener('click', async () => {
        try {
            processBtn.disabled = true;
            results.innerHTML = '<p>Processing documents...</p>';
            
            const formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            });
            
            const response = await fetch('/process-claim', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }
            
            const data = await response.json();
            displayResults(data);
            
        } catch (error) {
            results.innerHTML = `
                <div class="error">
                    ${error.message || 'An error occurred while processing the documents'}
                </div>
            `;
        } finally {
            processBtn.disabled = false;
        }
    });
    
    function displayResults(data) {
        const { documents, validation } = data;
        
        let html = '<h2>Processing Results</h2>';
        
        // Display validation status
        html += `
            <div class="validation-status ${validation.is_valid ? 'success' : 'error'}">
                Status: ${validation.is_valid ? 'Valid' : 'Invalid'}
            </div>
        `;
        
        // Display discrepancies if any
        if (validation.discrepancies.length > 0) {
            html += '<h3>Discrepancies</h3><ul>';
            validation.discrepancies.forEach(d => {
                html += `<li>${d}</li>`;
            });
            html += '</ul>';
        }
        
        // Display document details
        html += '<h3>Documents</h3>';
        documents.forEach(doc => {
            html += `
                <div class="document-details">
                    <h4>${doc.filename}</h4>
                    <p>Type: ${doc.type}</p>
                    <pre>${JSON.stringify(doc.data, null, 2)}</pre>
                </div>
            `;
        });
        
        results.innerHTML = html;
    }
}); 