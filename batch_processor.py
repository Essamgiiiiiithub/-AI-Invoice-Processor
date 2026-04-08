"""Batch processing utility for handling multiple files concurrently."""

import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from ocr_engine import extract_text
from ai_extractor import extract_document_data
from data_handler import save_invoices_batch


class DocumentProcessor:
    """Process multiple documents with concurrent processing."""
    
    def __init__(self, max_workers=3):
        """Initialize processor with thread pool size."""
        self.max_workers = max_workers
        self.results = []
        self.errors = []
    
    def process_files(self, uploaded_files, callback=None):
        """
        Process multiple uploaded files concurrently.
        
        Args:
            uploaded_files: List of uploaded file objects
            callback: Optional callback function to report progress
        
        Returns:
            tuple: (results_list, errors_list)
        """
        self.results = []
        self.errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {}
            
            # Submit all tasks
            for uploaded_file in uploaded_files:
                future = executor.submit(self._process_single_file, uploaded_file)
                future_to_file[future] = uploaded_file.name
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_file):
                file_name = future_to_file[future]
                try:
                    data, error = future.result()
                    if error:
                        self.errors.append((file_name, error))
                    else:
                        self.results.append((data, file_name))
                    
                    completed += 1
                    if callback:
                        callback(completed, len(uploaded_files), file_name)
                
                except Exception as e:
                    self.errors.append((file_name, str(e)))
                    if callback:
                        callback(completed + 1, len(uploaded_files), file_name)
        
        return self.results, self.errors
    
    def _process_single_file(self, uploaded_file):
        """Process a single file and return extracted data or error."""
        try:
            # Save uploaded file temporarily
            file_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Extract text
            text, error = extract_text(file_path)
            if error:
                return None, error
            
            if not text:
                return None, "No text found. Try a clearer photo."
            
            # Extract data with AI
            data = extract_document_data(text)
            return data, None
        
        except Exception as e:
            return None, f"Processing error: {str(e)}"
    
    def save_batch(self):
        """Save all results to database in batch."""
        if not self.results:
            return False
        
        try:
            data_list = [data for data, _ in self.results]
            from data_handler import save_invoices_batch
            save_invoices_batch(data_list)
            return True
        except Exception as e:
            print(f"❌ Batch save error: {e}")
            return False
    
    def get_summary(self):
        """Get processing summary."""
        return {
            "processed": len(self.results),
            "failed": len(self.errors),
            "total": len(self.results) + len(self.errors)
        }
