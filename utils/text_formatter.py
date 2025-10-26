# utils/text_formatter.py - ENHANCED VERSION
import html
import re
from typing import List, Dict

class UltimateTextFormatter:
    """
    ULTIMATE text formatter with perfect HTML and plain text support
    """
    
    @staticmethod
    def format_text(text: str, format_type: str = 'plain') -> str:
        """
        Main formatting function - UPDATED for perfect output
        
        Args:
            text: Extracted text to format
            format_type: 'plain' or 'html'
        """
        if not text:
            return ""
            
        format_type = format_type.lower()
        
        try:
            if format_type == 'html':
                return UltimateTextFormatter.format_html_perfect(text)
            else:  # plain
                return UltimateTextFormatter.format_plain_clean(text)
                
        except Exception as e:
            print(f"Formatting error: {e}")
            return text
    
    @staticmethod
    def format_plain_clean(text: str) -> str:
        """
        Clean plain text formatting - PERFECT for OCR output
        """
        if not text:
            return ""
        
        # Enhanced cleaning for OCR artifacts
        cleaned_text = UltimateTextFormatter.clean_ocr_artifacts(text)
        
        # Split by paragraphs (double newlines)
        paragraphs = cleaned_text.split('\n\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Clean each paragraph while preserving structure
                cleaned_paragraph = UltimateTextFormatter._clean_paragraph_enhanced(paragraph)
                if cleaned_paragraph:
                    cleaned_paragraphs.append(cleaned_paragraph)
        
        # Join with proper paragraph spacing
        result = '\n\n'.join(cleaned_paragraphs)
        
        # Final cleanup
        return result.strip()
    
    @staticmethod
    def format_html_perfect(text: str) -> str:
        """
        PERFECT HTML formatting with preserved structure
        """
        if not text:
            return ""
        
        try:
            # Enhanced cleaning
            cleaned_text = UltimateTextFormatter.clean_ocr_artifacts(text)
            
            # Handle multiple spaces and line breaks perfectly
            safe_text = html.escape(cleaned_text)
            
            # Preserve multiple spaces
            safe_text = safe_text.replace('  ', ' &nbsp;')
            
            # Handle line breaks properly
            lines = safe_text.split('\n')
            formatted_lines = []
            
            for line in lines:
                stripped_line = line.strip()
                if stripped_line:
                    # Replace multiple spaces within lines
                    formatted_line = stripped_line.replace('  ', ' &nbsp;')
                    formatted_lines.append(formatted_line)
                else:
                    # Empty line becomes paragraph break
                    formatted_lines.append('')
            
            # Build final HTML
            if len(formatted_lines) == 1:
                # Single line - use simple format
                return formatted_lines[0]
            else:
                # Multiple lines - use pre format for perfect preservation
                return '<pre>' + '\n'.join(formatted_lines) + '</pre>'
            
        except Exception as e:
            print(f"HTML formatting error: {e}")
            return f"<pre>{html.escape(text)}</pre>"
    
    @staticmethod
    def clean_ocr_artifacts(text: str) -> str:
        """Advanced OCR text cleaning for garbage patterns"""
        if not text:
            return text
            
        cleaned = text
        
        # Remove common OCR garbage patterns
        garbage_patterns = [
            r'[_\-\|]{5,}',  # Multiple underscores, dashes, pipes
            r'\*{3,}',       # Multiple asterisks
            r'\.{4,}',       # Multiple dots
            r'[ ]{3,}',      # Multiple spaces (more than 2)
        ]
        
        for pattern in garbage_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Fix common OCR mistakes (conservative approach)
        corrections = [
            (r'(?<=[A-Za-z])\|(?=[A-Za-z])', 'I'),  # Pipe between letters -> I
            (r'\b0(?=[A-Za-z])', 'O'),              # 0 before letters -> O
            (r'(?<=[A-Za-z])1\b', 'I'),             # 1 after letters -> I
        ]
        
        for pattern, replacement in corrections:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Normalize whitespace (preserve line breaks)
        lines = cleaned.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Clean each line individually
            cleaned_line = ' '.join(line.split())  # Normalize internal spaces
            cleaned_lines.append(cleaned_line)
        
        # Rebuild text
        cleaned = '\n'.join(cleaned_lines)
        
        return cleaned.strip()
    
    @staticmethod
    def _clean_paragraph_enhanced(paragraph: str) -> str:
        """Enhanced paragraph cleaning while preserving meaning"""
        lines = paragraph.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                line = re.sub(r'\s+', ' ', line)  # Normalize spaces
                line = UltimateTextFormatter._fix_bullets_enhanced(line)
                line = UltimateTextFormatter._fix_common_errors_enhanced(line)
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    @staticmethod
    def _fix_bullets_enhanced(line: str) -> str:
        """Enhanced bullet point detection"""
        bullet_patterns = [
            (r'^[eE]\s+', '• '),
            (r'^[oO0]\s+', '• '),
            (r'^[·●○▪■▶➢✓✔→\-]\s*', '• '),
            (r'^\.\s+', '• '),
            (r'^\*\s+', '• '),
            (r'^>\s+', '• '),
        ]
        
        for pattern, replacement in bullet_patterns:
            if re.match(pattern, line):
                line = re.sub(pattern, replacement, line)
                break
        
        return line
    
    @staticmethod
    def _fix_common_errors_enhanced(line: str) -> str:
        """Enhanced common OCR character error fixing"""
        corrections = [
            (r'\|\s*', 'I'),
            (r'\[\s*', 'I'),
            (r'\]\s*', 'I'),
            (r'\(\s*', 'I'),
            (r'\)\s*', 'I'),
            (r'\.\s*\.\s*\.', '...'),
        ]
        
        for pattern, replacement in corrections:
            line = re.sub(pattern, replacement, line)
        
        return line
    
    @staticmethod
    def split_long_message(text: str, max_length: int = 4000) -> List[str]:
        """Split long messages for Telegram while preserving paragraphs"""
        if len(text) <= max_length:
            return [text]
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        parts = []
        current_part = ""
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed limit
            if current_part and len(current_part) + len(paragraph) + 4 > max_length:
                parts.append(current_part.strip())
                current_part = paragraph
            else:
                if current_part:
                    current_part += '\n\n' + paragraph
                else:
                    current_part = paragraph
        
        # Add the final part
        if current_part:
            parts.append(current_part.strip())
        
        return parts

    @staticmethod
    def analyze_text_structure(text: str) -> Dict:
        """Analyze text structure for quality reporting"""
        if not text:
            return {}
        
        paragraphs = text.split('\n\n')
        total_paragraphs = len([p for p in paragraphs if p.strip()])
        
        # Count words and lines
        words = text.split()
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Calculate metrics
        word_count = len(words)
        line_count = len(non_empty_lines)
        avg_words_per_paragraph = word_count / total_paragraphs if total_paragraphs > 0 else 0
        
        return {
            'total_paragraphs': total_paragraphs,
            'word_count': word_count,
            'line_count': line_count,
            'avg_words_per_paragraph': round(avg_words_per_paragraph, 1),
            'structure_quality': 'Excellent' if avg_words_per_paragraph > 15 else 'Good' if avg_words_per_paragraph > 8 else 'Fair'
        }

# Global instance
ultimate_text_formatter = UltimateTextFormatter()

# Backward compatibility
TextFormatter = UltimateTextFormatter