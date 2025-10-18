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
            # Only add non-empty lines
            if cleaned_line.strip():
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
            
            # Preserve line breaks and formatting
            formatted_text = escaped_text.replace('\n', '<br>')
            
            # Use <pre> tag for perfect formatting preservation
            # This makes text easily copyable while preserving all formatting
            html_text = f"<pre>{formatted_text}</pre>"
            
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
        """Split long messages for Telegram with intelligent paragraph handling"""
        if len(text) <= max_length:
            return [text]
        
        # For HTML content, use different splitting
        if text.startswith('<pre>') and text.endswith('</pre>'):
            return TextFormatter._split_html_message(text, max_length)
        
        # Split by paragraphs to maintain readability for plain text
        paragraphs = text.split('\n\n')
        parts = []
        current_part = ""
        
        for paragraph in paragraphs:
            # If paragraph itself is too long, split by lines
            if len(paragraph) > max_length:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = ""
                
                # Split the long paragraph by lines
                lines = paragraph.split('\n')
                temp_part = ""
                for line in lines:
                    if len(temp_part) + len(line) + 1 > max_length and temp_part:
                        parts.append(temp_part.strip())
                        temp_part = line
                    else:
                        if temp_part:
                            temp_part += '\n' + line
                        else:
                            temp_part = line
                if temp_part:
                    parts.append(temp_part.strip())
            else:
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
    
    @staticmethod
    def _split_html_message(html_text, max_length):
        """Split HTML messages while preserving structure"""
        if len(html_text) <= max_length:
            return [html_text]
        
        # Extract content between <pre> tags
        content = html_text[5:-6]  # Remove <pre> and </pre>
        
        # Split the content
        plain_parts = TextFormatter.split_long_message(content, max_length - 10)  # Reserve space for tags
        
        # Wrap each part in <pre> tags
        html_parts = [f"<pre>{part}</pre>" for part in plain_parts]
        
        return html_parts
    
    @staticmethod
    def get_text_stats(text):
        """Get statistics about the extracted text"""
        if not text:
            return {
                'characters': 0,
                'words': 0,
                'lines': 0,
                'language_hint': 'unknown'
            }
        
        lines = text.split('\n')
        words = text.split()
        
        # Simple language detection based on character ranges
        amharic_chars = sum(1 for c in text if '\u1200' <= c <= '\u137F')
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        total_chars = len(text)
        
        language_hint = 'unknown'
        if total_chars > 0:
            if amharic_chars / total_chars > 0.3:
                language_hint = 'Amharic'
            elif english_chars / total_chars > 0.6:
                language_hint = 'English'
            elif english_chars > 0:
                language_hint = 'Mixed'
        
        return {
            'characters': len(text),
            'words': len(words),
            'lines': len([line for line in lines if line.strip()]),
            'language_hint': language_hint
        }