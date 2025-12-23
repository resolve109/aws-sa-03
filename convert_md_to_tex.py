#!/usr/bin/env python3
"""
Markdown to LaTeX converter for AWS Study Guide
"""
import re

def escape_latex(text):
    """Escape special LaTeX characters"""
    # Order matters! & must be escaped first, then other chars
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def convert_bold(text):
    """Convert **bold** to \textbf{bold}"""
    return re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', text)

def convert_inline_code(text):
    """Convert `code` to \texttt{code}"""
    return re.sub(r'`([^`]+)`', r'\\texttt{\1}', text)

def process_line(line, escaped=True):
    """Process a single line with escaping and formatting"""
    if escaped:
        line = escape_latex(line)
    line = convert_bold(line)
    line = convert_inline_code(line)
    return line

def get_indent_level(line):
    """Get the indentation level (number of leading spaces / 2)"""
    stripped = line.lstrip()
    if not stripped:
        return 0
    spaces = len(line) - len(stripped)
    return spaces // 2

def convert_markdown_to_latex(md_content):
    """Convert markdown content to LaTeX"""
    lines = md_content.split('\n')

    latex_parts = []

    # LaTeX preamble
    preamble = r'''\documentclass[11pt,a4paper]{report}

% Packages
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=1in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{parskip}

% Hyperref setup
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan,
    pdftitle={AWS Solutions Architect Study Guide},
    pdfauthor={},
}

% Custom section formatting
\titleformat{\chapter}[display]
    {\normalfont\huge\bfseries}{\chaptertitlename\ \thechapter}{20pt}{\Huge}
\titlespacing*{\chapter}{0pt}{0pt}{20pt}

% Header/Footer
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\leftmark}
\fancyhead[R]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% List settings for better formatting
\setlist[itemize]{topsep=2pt, partopsep=0pt, parsep=0pt, itemsep=2pt}
\setlist[itemize,1]{label=\textbullet}
\setlist[itemize,2]{label=--}
\setlist[itemize,3]{label=*}
\setlist[itemize,4]{label=$\cdot$}

\begin{document}

'''
    latex_parts.append(preamble)

    i = 0
    in_list = False
    list_depth = 0
    current_list_depths = []
    skip_toc = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines but close lists if needed
        if not stripped:
            if in_list:
                # Close all open lists
                while current_list_depths:
                    latex_parts.append('\\end{itemize}\n')
                    current_list_depths.pop()
                in_list = False
            latex_parts.append('\n')
            i += 1
            continue

        # Skip Table of Contents section in markdown (we'll generate it with LaTeX)
        if stripped == '## Table of Contents':
            skip_toc = True
            i += 1
            continue

        if skip_toc:
            # Skip until we hit the next ## section
            if stripped.startswith('## ') and stripped != '## Table of Contents':
                skip_toc = False
            else:
                i += 1
                continue

        # Close lists before headers
        if stripped.startswith('#'):
            while current_list_depths:
                latex_parts.append('\\end{itemize}\n')
                current_list_depths.pop()
            in_list = False

        # Main title
        if stripped.startswith('# ') and not stripped.startswith('## '):
            title = stripped[2:]
            title = escape_latex(title)
            latex_parts.append(f'\\title{{{title}}}\n')
            latex_parts.append('\\date{\\today}\n')
            latex_parts.append('\\maketitle\n\n')
            latex_parts.append('\\tableofcontents\n')
            latex_parts.append('\\newpage\n\n')
            i += 1
            continue

        # Chapter (## sections become chapters)
        if stripped.startswith('## '):
            section_title = stripped[3:]
            section_title = escape_latex(section_title)
            latex_parts.append(f'\n\\chapter{{{section_title}}}\n\n')
            i += 1
            continue

        # Section (### sections become sections)
        if stripped.startswith('### '):
            section_title = stripped[4:]
            section_title = escape_latex(section_title)
            latex_parts.append(f'\n\\section{{{section_title}}}\n\n')
            i += 1
            continue

        # Subsection (#### would become subsection)
        if stripped.startswith('#### '):
            section_title = stripped[5:]
            section_title = escape_latex(section_title)
            latex_parts.append(f'\n\\subsection{{{section_title}}}\n\n')
            i += 1
            continue

        # List items
        if stripped.startswith('- ') or stripped.startswith('* '):
            indent = get_indent_level(line)
            content = stripped[2:]
            content = process_line(content)

            if not in_list:
                # Start new list
                latex_parts.append('\\begin{itemize}\n')
                current_list_depths = [indent]
                in_list = True
            else:
                # Handle indentation changes
                if indent > current_list_depths[-1]:
                    # Deeper nesting
                    latex_parts.append('\\begin{itemize}\n')
                    current_list_depths.append(indent)
                elif indent < current_list_depths[-1]:
                    # Going back up
                    while current_list_depths and indent < current_list_depths[-1]:
                        latex_parts.append('\\end{itemize}\n')
                        current_list_depths.pop()
                    if not current_list_depths:
                        current_list_depths = [indent]

            latex_parts.append(f'  \\item {content}\n')
            i += 1
            continue

        # Numbered list items
        if re.match(r'^\d+\.\s', stripped):
            # For now, treat numbered lists as itemize
            content = re.sub(r'^\d+\.\s', '', stripped)
            content = process_line(content)

            if not in_list:
                latex_parts.append('\\begin{itemize}\n')
                current_list_depths = [0]
                in_list = True

            latex_parts.append(f'  \\item {content}\n')
            i += 1
            continue

        # Regular paragraph text
        if in_list:
            # Check if this is a continuation of a list item
            if line.startswith('    ') or line.startswith('\t'):
                # This is likely a continuation - append to previous item
                content = process_line(stripped)
                latex_parts.append(f'    {content}\n')
                i += 1
                continue
            else:
                # Close lists and treat as paragraph
                while current_list_depths:
                    latex_parts.append('\\end{itemize}\n')
                    current_list_depths.pop()
                in_list = False

        # Regular text
        content = process_line(stripped)
        latex_parts.append(f'{content}\n\n')
        i += 1

    # Close any remaining open lists
    while current_list_depths:
        latex_parts.append('\\end{itemize}\n')
        current_list_depths.pop()

    # Document end
    latex_parts.append('\n\\end{document}\n')

    return ''.join(latex_parts)

def main():
    # Read the markdown file
    with open('aws-study-guide.md', 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert to LaTeX
    latex_content = convert_markdown_to_latex(md_content)

    # Write the LaTeX file
    with open('aws-study-guide.tex', 'w', encoding='utf-8') as f:
        f.write(latex_content)

    print("Conversion complete! Output saved to aws-study-guide.tex")

if __name__ == '__main__':
    main()
