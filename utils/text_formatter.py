import html
import re

class TextFormatter:
    
    @staticmethod
    def format_plain(text):
        """Format text as plain text with enhanced cleaning"""
        if not text:
            return ""
        # Remove excessive whitespace but preserve structure
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(line for line in lines if line)
    
    @staticmethod
    def format_markdown(text):
        """
        Enhanced Markdown formatting with better escaping
        """
        if not text:
            return ""
        
        # Enhanced escape characters for MarkdownV2
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        
        def escape_text(txt):
            for char in escape_chars:
                txt = txt.replace(char, f'\\{char}')
            return txt
        
        try:
            # Enhanced line processing
            lines = text.split('\n')
            escaped_lines = []
            
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    escaped_lines.append("")
                    continue
                
                # Escape the line
                escaped_line = escape_text(line)
                
                # Preserve list-like structures
                if escaped_line.strip().startswith(('-', '*', '•')):
                    escaped_line = f"• {escaped_line.lstrip('-*• ')}"
                
                escaped_lines.append(escaped_line)
            
            return '\n'.join(escaped_lines)
        except Exception as e:
            # If Markdown fails, return plain text
            return text
    
    @staticmethod
    def format_html(text):
        """Enhanced HTML formatting with Telegram-compatible tags only"""
        if not text:
            return ""
        
        try:
            # Escape HTML entities first
            escaped_text = html.escape(text)
            
            # Enhanced line processing - use Telegram supported tags only
            lines = escaped_text.split('\n')
            html_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Use <b>, <i>, <u>, <code>, <pre> tags only (Telegram supported)
                    # For paragraphs, we'll use bold for emphasis
                    if len(line) > 50:  # Long lines as paragraphs
                        html_lines.append(f"<b>{line}</b>")
                    else:
                        html_lines.append(f"<i>{line}</i>")
                else:
                    html_lines.append("<br>")
            
            formatted_text = '\n'.join(html_lines)
            
            # Use <pre> tag for code-like formatting (Telegram supports this)
            return f"<pre>{formatted_text}</pre>"
        except:
            # Fallback to plain text in <pre> tags
            return f"<pre>{html.escape(text)}</pre>"
    
    @staticmethod
    def format_text(text, format_type='plain'):
        """Enhanced text formatting with better error handling"""
        if not text:
            return ""
            
        format_type = format_type.lower()
        
        try:
            if format_type == 'markdown':
                return TextFormatter.format_markdown(text)
            elif format_type == 'html':
                return TextFormatter.format_html(text)
            else:  # plain or any other type
                return TextFormatter.format_plain(text)
        except Exception as e:
            # Enhanced error handling
            print(f"Formatting error: {e}")
            return text