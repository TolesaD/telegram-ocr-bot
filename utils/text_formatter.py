# utils/text_formatter.py
import html
import re

class TextFormatter:
    
    @staticmethod
    def format_plain(text):
        """Format text as plain text with structure preservation"""
        if not text:
            return ""
        
        # Preserve original line breaks and spacing
        lines = text.split('\n')
        
        # Clean each line but maintain original structure
        cleaned_lines = []
        for line in lines:
            # Remove excessive internal whitespace but preserve line structure
            cleaned_line = ' '.join(line.split())
            cleaned_lines.append(cleaned_line)
        
        # Join back with original line breaks
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def format_html(text):
        """Enhanced HTML formatting with copy-friendly output"""
        if not text:
            return ""
        
        try:
            # Escape HTML entities
            escaped_text = html.escape(text)
            
            # Process lines for better structure
            lines = escaped_text.split('\n')
            html_lines = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    # For better copy-paste, use simple formatting
                    # Use monospace font and preserve spaces
                    html_lines.append(f"<code>{line}</code>")
                else:
                    # Preserve paragraph breaks
                    html_lines.append("<br>")
            
            # Use <pre> tag for better formatting but make it copy-friendly
            formatted_text = '\n'.join(html_lines)
            
            # Return with minimal styling for easy copying
            return formatted_text
            
        except Exception as e:
            print(f"HTML formatting error: {e}")
            # Fallback to simple preformatted text
            return f"<pre>{html.escape(text)}</pre>"
    
    @staticmethod
    def format_text(text, format_type='plain'):
        """Enhanced text formatting with better error handling"""
        if not text:
            return ""
            
        format_type = format_type.lower()
        
        try:
            if format_type == 'html':
                formatted = TextFormatter.format_html(text)
                # Ensure the HTML is copy-friendly
                return formatted
            else:  # plain or any other type
                return TextFormatter.format_plain(text)
        except Exception as e:
            print(f"Formatting error: {e}")
            return text
    
    @staticmethod
    def split_long_message(text, max_length=4000):
        """Split long messages for Telegram"""
        if len(text) <= max_length:
            return [text]
        
        parts = []
        while text:
            if len(text) <= max_length:
                parts.append(text)
                break
            
            # Find the last newline within the limit
            split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                # No newline found, split at space
                split_pos = text.rfind(' ', 0, max_length)
            if split_pos == -1:
                # No space found, force split
                split_pos = max_length
            
            parts.append(text[:split_pos])
            text = text[split_pos:].lstrip()
        
        return parts