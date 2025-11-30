# Documentation

This directory contains the MkDocs documentation for the Rural Medical AI Kiosk.

## Setup

Install MkDocs and dependencies using `uv`:

```bash
# Install MkDocs and plugins
uv pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin
```

## Running Locally

Start the development server:

```bash
mkdocs serve
```

The documentation will be available at [http://localhost:8000](http://localhost:8000)

## Building

Build the static site:

```bash
mkdocs build
```

Output will be in the `site/` directory.

## Deployment

### GitHub Pages

```bash
# Deploy to GitHub Pages
mkdocs gh-deploy
```

### Manual Deployment

```bash
# Build the site
mkdocs build

# Deploy the site/ directory to your hosting platform
rsync -avz site/ user@server:/var/www/docs/
```

## Structure

```
docs/
├── index.md                    # Homepage
├── getting-started/            # Getting started guides
│   ├── quick-start.md
│   ├── installation.md
│   ├── configuration.md
│   └── testing.md
├── architecture/               # System architecture
│   ├── overview.md
│   ├── frontend.md
│   ├── backend.md
│   ├── google-adk-agent.md
│   ├── mcp-tools.md
│   └── data-flow.md
├── features/                   # Feature documentation
│   ├── soap-workflow.md
│   ├── voice-interface.md
│   ├── image-analysis.md
│   ├── report-generation.md
│   ├── rag-similarity.md
│   └── multi-language.md
├── development/                # Development guides
│   ├── frontend.md
│   ├── backend.md
│   ├── api-reference.md
│   ├── custom-components.md
│   └── testing-guide.md
├── deployment/                 # Deployment guides
│   ├── production.md
│   ├── environment.md
│   ├── security.md
│   └── monitoring.md
├── reference/                  # Reference documentation
│   ├── soap-framework.md
│   ├── icd10-codes.md
│   ├── medical-safety.md
│   └── troubleshooting.md
└── stylesheets/               # Custom CSS
    └── extra.css
```

## Writing Documentation

### Markdown Guidelines

- Use clear, concise language
- Include code examples
- Add diagrams where helpful (Mermaid supported)
- Use admonitions for important notes

### Admonitions

```markdown
!!! note "Title"
    This is a note

!!! warning "Important"
    This is a warning

!!! tip "Pro Tip"
    This is a helpful tip
```

### Code Blocks

```markdown
\`\`\`python
def hello():
    print("Hello, World!")
\`\`\`

\`\`\`bash
curl http://localhost:8000/health
\`\`\`
```

### Mermaid Diagrams

```markdown
\`\`\`mermaid
graph LR
    A[Frontend] --> B[Backend]
    B --> C[Database]
\`\`\`
```

### Links

```markdown
[Link text](relative/path/to/page.md)
[External link](https://example.com)
```

## Contributing

When adding new documentation:

1. Create `.md` file in appropriate directory
2. Add to `nav` section in `mkdocs.yml`
3. Follow existing structure and style
4. Test locally with `mkdocs serve`
5. Commit changes

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Mermaid Diagrams](https://mermaid-js.github.io/)
