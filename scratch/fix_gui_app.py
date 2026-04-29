# -*- coding: utf-8 -*-
import sys

def recover_thai(text):
    try:
        # The text was decoded as latin-1 from what was likely UTF-8 + some bad bytes
        # or it was cp874.
        # If it was mojibake of UTF-8:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def fix_gui_app(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for i, line in enumerate(lines):
        # Fix the broken line 161 (0-indexed 160)
        if "ctk.CTkButton(self.ctx_menu, text    def _manual_paste_handler" in line:
            # It seems a line was cut off or joined
            new_lines.append('        ctk.CTkButton(self.ctx_menu, text="📋 วาง (Paste)", height=28, fg_color="transparent", anchor="w", \n')
            new_lines.append('                      command=self._ctx_paste).pack(fill="x")\n')
            new_lines.append('\n')
            new_lines.append('    def _manual_paste_handler(self, event=None):\n')
            continue
            
        # Fix the line 181 (0-indexed 180) which has the bad character
        if "£à¸—à¸µà¹ˆ StringVar à¹‚à¸”à¸¢à¸•à¸£à¸‡\"\"\"" in line or "£" in line and "StringVar" in line:
            new_lines.append('        """วางลงที่ StringVar โดยตรง"""\n')
            continue

        # Recover Thai for other lines if they look like mojibake
        if "à" in line:
            recovered = recover_thai(line)
            new_lines.append(recovered)
        else:
            new_lines.append(line)

    # Re-write the file
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    fix_gui_app("gui_app.py")
