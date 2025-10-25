# utils/text_formatter.py
import html
import re
from typing import List, Dict

class TextFormatter:
    """
    Smart text formatter that maintains paragraph structure
    and improves readability while preserving meaning
    """
    
    @staticmethod
    def format_plain(text: str) -> str:
        """
        Clean plain text with proper paragraph structure
        """
        if not text:
            return ""
        
        # Split by paragraphs (double newlines)
        paragraphs = text.split('\n\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Clean the paragraph while preserving meaning
                cleaned_paragraph = TextFormatter._clean_paragraph(paragraph)
                if cleaned_paragraph:
                    cleaned_paragraphs.append(cleaned_paragraph)
        
        # Join with proper paragraph spacing
        return '\n\n'.join(cleaned_paragraphs)
    
    @staticmethod
    def _clean_paragraph(paragraph: str) -> str:
        """Clean a single paragraph while preserving meaning"""
        # Split into lines and clean each line
        lines = paragraph.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                # Fix common OCR issues without changing meaning
                cleaned_line = re.sub(r'\s+', ' ', cleaned_line)  # Normalize spaces
                cleaned_line = TextFormatter._fix_bullets(cleaned_line)  # Fix bullet points
                cleaned_lines.append(cleaned_line)
        
        # Join lines with spaces to form a proper paragraph
        return ' '.join(cleaned_lines)
    
    @staticmethod
    def _fix_bullets(line: str) -> str:
        """Fix common bullet point OCR issues"""
        bullet_fixes = [
            (r'^[eE]\s+', '• '),
            (r'^[oO0]\s+', '• '),
            (r'^[·●○▪■▶➢✓✔→\-]\s*', '• '),
            (r'^\.\s+', '• '),
            (r'^\*\s+', '• '),
        ]
        
        for pattern, replacement in bullet_fixes:
            if re.match(pattern, line):
                line = re.sub(pattern, replacement, line)
                break
        
        return line
    
    @staticmethod
    def format_html(text: str) -> str:
        """
        HTML format that preserves paragraph structure
        """
        if not text:
            return ""
        
        try:
            # Split into paragraphs
            paragraphs = text.split('\n\n')
            html_paragraphs = []
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    escaped_paragraph = html.escape(paragraph.strip())
                    html_paragraphs.append(f"<p>{escaped_paragraph}</p>")
            
            return '\n'.join(html_paragraphs)
            
        except Exception as e:
            print(f"HTML formatting error: {e}")
            return f"<pre>{html.escape(text)}</pre>"
    
    @staticmethod
    def format_preserved(text: str) -> str:
        """
        Maximum preservation - returns text exactly as OCR extracted it
        """
        return text if text else ""
    
    @staticmethod
    def format_structured(text: str) -> str:
        """
        Intelligently structured format
        - Maintains paragraph structure
        - Fixes common OCR errors
        - Improves readability while preserving meaning
        """
        if not text:
            return ""
        
        return TextFormatter.format_plain(text)  # Use the same logic as plain format
    
    @staticmethod
    def format_text(text: str, format_type: str = 'structured') -> str:
        """
        Main formatting function
        
        Recommended format_type: 'structured' for best readability
        """
        if not text:
            return ""
            
        format_type = format_type.lower()
        
        try:
            if format_type == 'html':
                return TextFormatter.format_html(text)
            elif format_type == 'structured':
                return TextFormatter.format_structured(text)
            elif format_type == 'preserved':
                return TextFormatter.format_preserved(text)
            else:  # plain
                return TextFormatter.format_plain(text)
                
        except Exception as e:
            print(f"Formatting error: {e}")
            return text
    
    @staticmethod
    def split_long_message(text: str, max_length: int = 4000) -> List[str]:
        """Split long messages while preserving paragraph structure"""
        if len(text) <= max_length:
            return [text]
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        parts = []
        current_part = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed limit, start new part
            if current_part and len(current_part) + len(paragraph) + 4 > max_length:
                parts.append(current_part.strip())
                current_part = paragraph
            else:
                if current_part:
                    current_part += '\n\n' + paragraph
                else:
                    current_part = paragraph
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts

    @staticmethod
    def analyze_text_structure(text: str) -> Dict:
        """Analyze text structure and quality"""
        if not text:
            return {}
        
        paragraphs = text.split('\n\n')
        total_paragraphs = len([p for p in paragraphs if p.strip()])
        
        # Count words for readability assessment
        words = text.split()
        word_count = len(words)
        
        # Calculate average words per paragraph
        avg_words_per_paragraph = word_count / total_paragraphs if total_paragraphs > 0 else 0
        
        return {
            'total_paragraphs': total_paragraphs,
            'word_count': word_count,
            'avg_words_per_paragraph': round(avg_words_per_paragraph, 1),
            'readability_score': min(100, int(avg_words_per_paragraph * 2)),
            'structure_quality': 'Good' if avg_words_per_paragraph > 10 else 'Needs Improvement'
        }