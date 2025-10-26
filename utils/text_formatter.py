# utils/text_formatter.py
import html
import re
from typing import List, Dict

class TextFormatter:
    """
    Production text formatter with intelligent formatting options
    """
    
    @staticmethod
    def format_text(text: str, format_type: str = 'plain') -> str:
        """
        Main formatting function - UPDATED to match app.py usage
        
        Args:
            text: Extracted text to format
            format_type: 'plain' or 'html'
        """
        if not text:
            return ""
            
        format_type = format_type.lower()
        
        try:
            if format_type == 'html':
                return TextFormatter.format_html(text)
            else:  # plain
                return TextFormatter.format_plain(text)
                
        except Exception as e:
            print(f"Formatting error: {e}")
            return text
    
    @staticmethod
    def format_plain(text: str) -> str:
        """
        Clean plain text formatting
        """
        if not text:
            return ""
        
        # Split by paragraphs (double newlines)
        paragraphs = text.split('\n\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Clean each paragraph
                cleaned_paragraph = TextFormatter._clean_paragraph(paragraph)
                if cleaned_paragraph:
                    cleaned_paragraphs.append(cleaned_paragraph)
        
        # Join with proper paragraph spacing
        return '\n\n'.join(cleaned_paragraphs)
    
    @staticmethod
    def _clean_paragraph(paragraph: str) -> str:
        """Clean a single paragraph while preserving meaning"""
        lines = paragraph.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                line = re.sub(r'\s+', ' ', line)  # Normalize spaces
                line = TextFormatter._fix_bullets(line)
                line = TextFormatter._fix_common_errors(line)
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    @staticmethod
    def _fix_bullets(line: str) -> str:
        """Fix bullet point detection issues"""
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
    def _fix_common_errors(line: str) -> str:
        """Fix common OCR character errors"""
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
    def format_html(text: str) -> str:
        """
        HTML formatting for easy copying
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
        Maximum preservation - no changes to extracted text
        Returns exactly what OCR extracted
        """
        return text if text else ""
    
    @staticmethod
    def format_structured(text: str) -> str:
        """
        Intelligently structured format
        - Best readability while preserving structure
        - Recommended for most users
        """
        if not text:
            return ""
        
        return TextFormatter.format_plain(text)
    
    @staticmethod
    def format_text(text: str, format_type: str = 'structured') -> str:
        """
        Main formatting function
        
        Args:
            text: Extracted text to format
            format_type: 
                - 'structured': Best readability (recommended)
                - 'plain': Clean text
                - 'preserved': No changes
                - 'html': HTML format
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