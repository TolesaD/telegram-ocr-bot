import html
import config  # Import config directly

class TextFormatter:
    @staticmethod
    def format_plain(text):
        """Format text as plain text"""
        return text
    
    @staticmethod
    def format_markdown(text):
        """Format text as Markdown"""
        # Escape Markdown special characters
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        formatted_text = text
        for char in special_chars:
            formatted_text = formatted_text.replace(char, f'\\{char}')
        return formatted_text
    
    @staticmethod
    def format_html(text):
        """Format text as HTML"""
        # Escape HTML entities and wrap in pre tags
        escaped_text = html.escape(text)
        return f"<pre>{escaped_text}</pre>"
    
    @staticmethod
    def format_text(text, format_type='plain'):
        """Format text based on specified format type"""
        format_type = format_type.lower()
        
        if format_type == 'markdown':
            return TextFormatter.format_markdown(text)
        elif format_type == 'html':
            return TextFormatter.format_html(text)
        else:  # plain
            return TextFormatter.format_plain(text)