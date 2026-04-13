import re
import os

def main():
    filepath = 'sources/sources_index.md'
    outpath = 'project_context/context_extraction.md'

    # Ensure output directory exists (in case it is run from a fresh clone)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to extract paper title and its block of details
    # Matches from '## Paper X: title' until the next '## ' or end of file
    papers = re.findall(r'## Paper \d+: (.*?)\n(.*?)(?=\n## |\Z)', content, re.DOTALL)

    table_header = "# Context Extraction\n\n| Article Title | Authors | Social Problem(s) (In Detail) | Methods (In Detail) |\n|---|---|---|---|\n"
    rows = []

    for title, body in papers:
        # Sanitize pipes since they break markdown tables
        title = title.strip().replace('|', '-')
        authors = ''
        social_prob = ''
        method = ''
        opt_type = ''
        
        # Simple line-by-line parsing
        for line in body.split('\n'):
            line = line.strip()
            if line.startswith('- **Authors:**'): 
                authors = line.replace('- **Authors:**', '').strip().replace('|', ',')
            elif line.startswith('- **Social Problem(s):**'): 
                social_prob = line.replace('- **Social Problem(s):**', '').strip().replace('|', ',')
            elif line.startswith('- **Key Method:**'): 
                method = line.replace('- **Key Method:**', '').strip().replace('|', ',')
            elif line.startswith('- **Optimization Type:**'):
                opt_type = line.replace('- **Optimization Type:**', '').strip().replace('|', ',')
                
        # Combine optimization type and method for detailed methods column
        full_method = f"{opt_type} --- {method}" if opt_type else method
        
        rows.append(f"| {title} | {authors} | {social_prob} | {full_method} |")

    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(table_header + '\n'.join(rows))

    print(f"Done! Processed {len(papers)} papers and saved table to {outpath}.")

if __name__ == '__main__':
    main()
