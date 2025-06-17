# GitHub Pages Deployment

Deploy the documentation to GitHub Pages for easy access and sharing.

## Prerequisites

- GitHub repository with the documentation
- Admin access to the repository
- MkDocs installed locally for testing

## Quick Setup

### 1. Configure MkDocs for GitHub Pages

The `mkdocs.yml` file is already configured with the correct site URL:

```yaml
site_url: https://jmontp.github.io/agent-workflow/
repo_url: https://github.com/jmontp/agent-workflow
repo_name: jmontp/agent-workflow
```

### 2. Deploy Using MkDocs Command

From the repository root:

```bash
# Build and deploy to GitHub Pages
mkdocs gh-deploy --clean
```

This command will:
- Build the documentation site
- Create/update the `gh-pages` branch
- Push the generated site to GitHub

### 3. Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select **Deploy from a branch**
4. Choose **gh-pages** branch and **/ (root)** folder
5. Click **Save**

The documentation will be available at: `https://jmontp.github.io/agent-workflow/`

## Automated Deployment

### GitHub Actions Workflow

Create `.github/workflows/docs.yml` for automatic deployment:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main, master]
    paths:
      - 'docs_src/**'
      - 'mkdocs.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          pip install mkdocs-material
          pip install pymdown-extensions

      - name: Build and deploy
        run: mkdocs gh-deploy --force
```

### Manual Deployment Commands

For local development and testing:

```bash
# Preview locally
mkdocs serve

# Build static site
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy --clean

# Deploy with custom commit message
mkdocs gh-deploy -m "Update documentation"
```

## Custom Domain (Optional)

### 1. Configure DNS

If you have a custom domain, add a `CNAME` file:

```bash
# Add to docs_src/CNAME
echo "docs.yourdomain.com" > docs_src/CNAME
```

### 2. Update MkDocs Configuration

```yaml
site_url: https://docs.yourdomain.com/
```

### 3. Configure GitHub Pages

1. Go to **Settings** → **Pages**
2. Enter your custom domain
3. Enable **Enforce HTTPS**

## Troubleshooting

### Common Issues

**Pages not updating:**
- Check the Actions tab for deployment status
- Ensure the `gh-pages` branch exists
- Wait up to 10 minutes for changes to propagate

**404 errors:**
- Verify the site URL in `mkdocs.yml`
- Check that GitHub Pages is enabled
- Ensure the correct branch is selected

**Build failures:**
- Check that all plugins are installed
- Verify markdown syntax in documentation files
- Review GitHub Actions logs for errors

### Branch Protection

If your repository has branch protection rules:

1. Allow the GitHub Actions bot to push to `gh-pages`
2. Or create the branch manually and exempt it from protection
3. Use a personal access token with appropriate permissions

## Best Practices

### Content Organization

- Keep documentation source in `docs_src/`
- Use clear, descriptive filenames
- Maintain consistent navigation structure
- Include relative links between pages

### Performance Optimization

- Optimize images and media files
- Use MkDocs caching for faster builds
- Consider using a CDN for better global performance

### SEO and Accessibility

- Include meta descriptions in frontmatter
- Use proper heading hierarchy
- Add alt text for images
- Test with screen readers

### Maintenance

- Set up automated link checking
- Regular review and updates
- Monitor GitHub Pages usage limits
- Keep dependencies updated

## Advanced Configuration

### Custom Themes

Customize the Material theme:

```yaml
theme:
  name: material
  custom_dir: overrides
  palette:
    - scheme: default
      primary: custom-color
  logo: assets/logo.png
  favicon: assets/favicon.ico
```

### Analytics Integration

Add Google Analytics:

```yaml
extra:
  analytics:
    provider: google
    property: GA_MEASUREMENT_ID
```

### Social Media Cards

Configure Open Graph metadata:

```yaml
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/jmontp/agent-workflow
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/username
```

## Monitoring and Analytics

- Use GitHub repository insights
- Monitor page views in GitHub Pages settings
- Set up Google Analytics for detailed metrics
- Track user engagement and popular content

The documentation site will automatically update whenever changes are pushed to the main branch, ensuring the published docs stay current with development.