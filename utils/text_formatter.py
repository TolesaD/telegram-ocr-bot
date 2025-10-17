# utils/text_formatter.py
import html
import re

class TextFormatter:
    
    @staticmethod
    def format_plain(text):
        """
        Format as plain text with preserved structure
        - Maintains original line breaks and spacing
        - Preserves bullets and special characters
        - Clean but minimal processing
        """
        if not text:
            return ""
        
        # Preserve all original line breaks and structure
        lines = text.split('\n')
        
        # Clean each line minimally
        cleaned_lines = []
        for line in lines:
            # Remove excessive internal whitespace but preserve indentation
            cleaned_line = ' '.join(line.split())
            cleaned_lines.append(cleaned_line)
        
        # Join back with original line structure
        formatted_text = '\n'.join(cleaned_lines)
        
        return formatted_text
    
    @staticmethod
    def format_html(text):
        """
        Format as copy-friendly HTML
        - Uses <pre> tag for perfect formatting preservation
        - Easily copy-pasteable
        - Telegram compatible
        """
        if not text:
            return ""
        
        try:
            # Escape HTML entities
            escaped_text = html.escape(text)
            
            # Use <pre> tag for perfect formatting preservation
            # This makes text easily copyable while preserving all formatting
            html_text = f"<pre>{escaped_text}</pre>"
            
            return html_text
            
        except Exception as e:
            print(f"HTML formatting error: {e}")
            # Fallback to simple preformatted text
            return f"<pre>{html.escape(text)}</pre>"
    
    @staticmethod
    def format_text(text, format_type='plain'):
        """
        Main formatting function
        Defaults to plain text, with HTML as copiable alternative
        """
        if not text:
            return ""
            
        format_type = format_type.lower()
        
        try:
            if format_type == 'html':
                return TextFormatter.format_html(text)
            else:  # plain or any other type
                return TextFormatter.format_plain(text)
        except Exception as e:
            print(f"Formatting error: {e}")
            return text  # Return original text as fallback
    
    @staticmethod
    def split_long_message(text, max_length=4000):
        """Split long messages for Telegram"""
        if len(text) <= max_length:
            return [text]
        
        # Split by paragraphs to maintain readability
        paragraphs = text.split('\n\n')
        parts = []
        current_part = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed limit, start new part
            if len(current_part) + len(paragraph) + 2 > max_length and current_part:
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