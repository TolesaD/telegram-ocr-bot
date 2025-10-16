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
    def format_copiable(text):
        """Format text for easy copying with clean structure"""
        if not text:
            return ""
        # Clean text with preserved bullets and minimal formatting
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                # Preserve bullets
                if stripped.startswith(('•', '-', '*', '–')):
                    cleaned_lines.append(f"• {stripped.lstrip('•-*– ')}")
                else:
                    cleaned_lines.append(stripped)
            else:
                cleaned_lines.append("")
        return '\n'.join(cleaned_lines).rstrip()
    
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
                    if len(line) > 50:  # Long lines as paragraphs
                        html_lines.append(f"<b>{line}</b>")
                    else:
                        html_lines.append(f"<i>{line}</i>")
                else:
                    html_lines.append("<br>")
            
            formatted_text = '\n'.join(html_lines)
            
            # Use <pre> tag for code-like formatting
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
            if format_type == 'copiable':
                return TextFormatter.format_copiable(text)
            elif format_type == 'html':
                return TextFormatter.format_html(text)
            else:  # plain or any other type
                return TextFormatter.format_plain(text)
        except Exception as e:
            logger.error(f"Formatting error: {e}")
            return text