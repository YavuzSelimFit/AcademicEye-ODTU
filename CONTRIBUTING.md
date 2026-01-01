# Contributing Guide

Thank you for considering contributing to AcademicEye. This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Process](#development-process)
- [Code Standards](#code-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project aims to provide an open and welcoming environment for everyone. Please:

- Be respectful and constructive
- Welcome differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community

## How to Contribute

### Reporting Bugs

If you find a bug:

1. Check GitHub Issues to see if it has already been reported
2. If not, open a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected behavior
   - Screenshots if applicable
   - System information (Python version, OS, etc.)

### Suggesting Features

To propose a new feature:

1. Open a GitHub Issue with the "Feature Request" label
2. Explain:
   - The purpose and benefits
   - Use cases
   - Potential implementation approach

### Contributing Code

To contribute code:

1. Choose or create an issue
2. Comment on the issue to indicate you're working on it
3. Follow the Fork + Branch + PR workflow

## Development Process

### 1. Fork the Repository

```bash
# Click Fork on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/AcademicEye-ODTU.git
cd AcademicEye
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 4. Make Your Changes

- Write code
- Test thoroughly
- Update documentation if needed

### 5. Test Your Changes

```bash
# Clean database if needed
rm academic_memory.db

# Reinitialize
python database.py

# Run application
python app.py

# Test different scenarios
```

### 6. Commit and Push

```bash
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
```

### 7. Open a Pull Request

- Go to your fork on GitHub
- Click "Pull Request"
- Describe your changes
- Reference related issues (e.g., #123)

## Code Standards

### Python Style

Follow PEP 8 standards:

```python
# Good
def calculate_h_index(publications):
    """
    Calculate H-index from publication list.
    
    Args:
        publications: List of publication dictionaries
        
    Returns:
        int: H-index value
    """
    sorted_pubs = sorted(publications, key=lambda x: x['citations'], reverse=True)
    h = 0
    for i, pub in enumerate(sorted_pubs):
        if pub['citations'] >= i + 1:
            h = i + 1
    return h

# Avoid
def calcHIndex(pubs):
    s=sorted(pubs,key=lambda x:x['citations'],reverse=True)
    h=0
    for i,p in enumerate(s):
        if p['citations']>=i+1:h=i+1
    return h
```

### Docstrings

```python
def search_scopus_author(name, affiliation=None):
    """
    Search for author using Scopus API.
    
    Args:
        name (str): Full name of the author
        affiliation (str, optional): Institution name for filtering
        
    Returns:
        str: Scopus Author ID or None
        
    Raises:
        requests.HTTPError: If API request fails
        
    Example:
        >>> author_id = search_scopus_author("John Doe", "MIT")
        >>> print(author_id)
        '12345678900'
    """
    # Implementation
```

### Variable Naming

```python
# Preferred
user_profile = get_user_by_id(user_id)
publication_count = len(publications)

# Avoid
up = get_user_by_id(user_id)
cnt = len(publications)
```

### Error Handling

```python
# Good
try:
    data = get_scopus_publications(author_id)
    if not data:
        logger.warning(f"No publications found for author {author_id}")
        return []
    return data['publications']
except requests.HTTPError as e:
    logger.error(f"Scopus API error: {e}")
    return []
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return []

# Avoid
try:
    data = get_scopus_publications(author_id)
    return data['publications']
except:
    return []
```

## Commit Messages

Use Semantic Commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no behavior change)
- `refactor`: Code restructuring
- `test`: Adding/updating tests
- `chore`: Build/config changes

### Examples

```bash
# Good
git commit -m "feat(scopus): add department report generation"
git commit -m "fix(yok-bot): handle missing publication dates"
git commit -m "docs(readme): add installation instructions"

# Avoid
git commit -m "fixed stuff"
git commit -m "update"
git commit -m "changes"
```

### Detailed Commit

```bash
git commit -m "feat(career-engine): add fuzzy matching for publication titles

- Implement is_similar_title() function
- Use difflib.SequenceMatcher for comparison
- Add Jaccard similarity for token-based matching
- Set threshold to 0.85 for better accuracy

Closes #42"
```

## Pull Request Process

### PR Checklist

Before opening a PR, verify:

- [ ] Code follows PEP 8 standards
- [ ] Docstrings are included
- [ ] Changes have been tested
- [ ] README updated if necessary
- [ ] Commit messages are meaningful
- [ ] Branch is up to date (`git pull --rebase upstream main`)

### PR Template

```markdown
## Changes

- Added Scopus API integration
- Optimized YÖK bot
- Added new statistics to dashboard

## Related Issue

Closes #123

## Testing

- [x] Tested locally
- [x] Tested different user scenarios
- [ ] Unit tests written

## Screenshots

(Include if applicable)

## Additional Notes

Added 0.4 second delay for rate limiting.
```

### Review Process

1. Maintainer reviews the code
2. May request changes
3. Make requested changes and update PR
4. Once approved, PR will be merged

## Good First Issues

For newcomers to the project:

- Issues labeled `good-first-issue`
- Documentation improvements
- Writing tests
- Improving error messages
- UI/UX enhancements

## Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Semantic Commit Messages](https://www.conventionalcommits.org/)
- [Flask Best Practices](https://flask.palletsprojects.com/en/2.3.x/patterns/)
- [Python Docstring Conventions](https://peps.python.org/pep-0257/)

## Questions

- Use GitHub Discussions
- Open an issue
- Contact the maintainer

---

Thank you for your contributions.
