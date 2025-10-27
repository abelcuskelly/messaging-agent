# Deploying Demo to AI-Agency Repository

## Step 1: Copy Demo Files

Copy the demo files to your AI-Agency repository:

```bash
# From the messaging agent directory
cd AI-Agency-demo

# Copy files to AI-Agency repo
cp index.html /path/to/AI-Agency/agent-demo.html
```

## Step 2: Commit to AI-Agency

```bash
cd /path/to/AI-Agency
git add agent-demo.html
git commit -m "Add AI Agent interactive demo page"
git push origin main
```

## Step 3: Update Website Navigation

Add a "Try Demo" button to the main AI-Agency website (`index.html`):

```html
<a href="agent-demo.html" class="cta-button">
    Try Live Demo →
</a>
```

## Step 4: Publish

GitHub Pages will automatically deploy the demo:
- Live URL: https://abelcuskelly.github.io/AI-Agency/agent-demo.html

## Alternative: Subfolder Organization

For better organization, create a subfolder:

```bash
cd /path/to/AI-Agency
mkdir agent-demo
cp /path/to/AI-Agency-demo/index.html agent-demo/
git add agent-demo/
git commit -m "Add AI agent demo section"
git push origin main
```

## Testing

Visit the demo at:
- https://abelcuskelly.github.io/AI-Agency/agent-demo/index.html

Or if using root:
- https://abelcuskelly.github.io/AI-Agency/agent-demo.html
