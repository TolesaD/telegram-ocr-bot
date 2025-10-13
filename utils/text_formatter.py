import html
import re

class TextFormatter:
    
    @staticmethod
    def format_plain(text):
        """Format text as plain text"""
        if not text:
            return ""
        return text
    
    @staticmethod
    def format_markdown(text):
        """
        Format text as MarkdownV2 with PROPER escaping for Telegram
        Telegram MarkdownV2 requires escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !
        """
        if not text:
            return ""
        
        # Escape all MarkdownV2 special characters
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        
        def escape_text(txt):
            # Escape each special character
            for char in escape_chars:
                txt = txt.replace(char, f'\\{char}')
            return txt
        
        try:
            # Split into lines and escape each line
            lines = text.split('\n')
            escaped_lines = [escape_text(line) for line in lines]
            return '\n'.join(escaped_lines)
        except Exception as e:
            # If Markdown fails, return plain text
            return text
    
    @staticmethod
    def format_markdown_simple(text):
        """
        Simple Markdown formatting - only escapes the most problematic characters
        """
        if not text:
            return ""
        
        # Only escape the most essential characters that break parsing
        essential_chars = ['_', '*', '`', '[']
        
        formatted_text = text
        for char in essential_chars:
            formatted_text = formatted_text.replace(char, f'\\{char}')
        
        return formatted_text
    
    @staticmethod
    def format_html(text):
        """Format text as HTML"""
        if not text:
            return ""
        
        try:
            # Escape HTML entities
            escaped_text = html.escape(text)
            
            # Replace newlines with <br> tags for better formatting
            formatted_text = escaped_text.replace('\n', '<br>')
            
            return f"<pre>{formatted_text}</pre>"
        except:
            return f"<pre>{text}</pre>"
    
    @staticmethod
    def format_text(text, format_type='plain'):
        """Format text based on specified format type"""
        if not text:
            return ""
            
        format_type = format_type.lower()
        
        try:
            if format_type == 'markdown':
                return TextFormatter.format_markdown_simple(text)
            elif format_type == 'html':
                return TextFormatter.format_html(text)
            else:  # plain or any other type
                return TextFormatter.format_plain(text)
        except Exception as e:
            # If any formatting fails, return plain text
            return text