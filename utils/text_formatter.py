# utils/text_formatter.py
import html
import re

class TextFormatter:
    
    @staticmethod
    def format_plain(text):
        """
        Enhanced plain text formatting that preserves structure and handles Amharic
        """
        if not text:
            return ""
        
        # First, fix common bullet misdetections
        text = TextFormatter.fix_bullet_detection(text)
        
        # Preserve all original line breaks and structure
        lines = text.split('\n')
        
        # Enhanced cleaning that preserves structure
        cleaned_lines = []
        for line in lines:
            cleaned_line = TextFormatter._clean_line_preserve_structure(line)
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        # Join back with original line structure
        formatted_text = '\n'.join(cleaned_lines)
        
        return formatted_text
    
    @staticmethod
    def fix_bullet_detection(text):
        """Fix common OCR bullet misdetections"""
        if not text:
            return text
        
        # Common bullet misdetections and their corrections
        bullet_fixes = [
            (r'^e\s+', '• '),      # 'e ' at start of line -> bullet
            (r'^o\s+', '• '),      # 'o ' at start of line -> bullet  
            (r'^0\s+', '• '),      # '0 ' at start of line -> bullet
            (r'^c\s+', '• '),      # 'c ' at start of line -> bullet
            (r'^\.\s+', '• '),     # '. ' at start of line -> bullet
            (r'^-\s+', '• '),      # '- ' at start of line -> bullet
            (r'^\*\s+', '• '),     # '* ' at start of line -> bullet
        ]
        
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            fixed_line = line
            for pattern, replacement in bullet_fixes:
                fixed_line = re.sub(pattern, replacement, fixed_line)
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)
    
    @staticmethod
    def _clean_line_preserve_structure(line):
        """Clean line while preserving bullets, structure, and Amharic characters"""
        if not line.strip():
            return ""
        
        # Preserve bullet points and special characters at line start
        bullet_chars = ['•', '·', '∙', '○', '●', '▪', '▫', '-', '*', '→', '⇒']
        
        has_bullet = False
        preserved_prefix = ""
        
        # Check if line starts with a bullet
        if line and line[0] in bullet_chars:
            has_bullet = True
            preserved_prefix = line[0]
            line_content = line[1:].lstrip()  # Remove bullet and leading space after it
        else:
            line_content = line
        
        # For Amharic text, be more careful with cleaning to preserve characters
        amharic_chars = sum(1 for c in line_content if '\u1200' <= c <= '\u137F')
        total_chars = len(line_content.strip())
        
        if total_chars > 0 and (amharic_chars / total_chars) > 0.3:
            # This is likely Amharic text, preserve original spacing more carefully
            cleaned_line = ' '.join(line_content.split())
        else:
            # For other languages, normal cleaning
            cleaned_line = ' '.join(line_content.split())
        
        # Restore bullet if present
        if has_bullet and cleaned_line:
            return preserved_prefix + ' ' + cleaned_line
        elif cleaned_line:
            return cleaned_line
        else:
            return ""
    
    @staticmethod
    def format_html(text):
        """
        Enhanced HTML formatting for perfect copy-paste
        """
        if not text:
            return ""
        
        try:
            # First fix bullets in the text
            text = TextFormatter.fix_bullet_detection(text)
            
            # Escape HTML entities
            escaped_text = html.escape(text)
            
            # Enhanced HTML with better formatting preservation
            html_text = f"<pre>{escaped_text}</pre>"
            
            return html_text
            
        except Exception as e:
            print(f"HTML formatting error: {e}")
            # Fallback to simple preformatted text
            return f"<pre>{html.escape(text)}</pre>"
    
    @staticmethod
    def format_text(text, format_type='plain'):
        """
        Enhanced main formatting function with bullet fixes
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
        """Enhanced message splitting that preserves paragraphs"""
        if len(text) <= max_length:
            return [text]
        
        # Enhanced splitting that respects paragraph boundaries
        paragraphs = text.split('\n\n')
        parts = []
        current_part = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed limit, start new part
            if len(current_part) + len(paragraph) + 4 > max_length and current_part:
                parts.append(current_part.strip())
                current_part = paragraph
            else:
                if current_part:
                    current_part += '\n\n' + paragraph
                else:
                    current_part = paragraph
        
        # Don't forget the last part
        if current_part:
            parts.append(current_part.strip())
        
        # If any part is still too long, split by lines
        final_parts = []
        for part in parts:
            if len(part) > max_length:
                # Split by lines for very long paragraphs
                lines = part.split('\n')
                current_chunk = ""
                
                for line in lines:
                    if len(current_chunk) + len(line) + 1 > max_length and current_chunk:
                        final_parts.append(current_chunk.strip())
                        current_chunk = line
                    else:
                        if current_chunk:
                            current_chunk += '\n' + line
                        else:
                            current_chunk = line
                
                if current_chunk:
                    final_parts.append(current_chunk.strip())
            else:
                final_parts.append(part)
        
        return final_parts