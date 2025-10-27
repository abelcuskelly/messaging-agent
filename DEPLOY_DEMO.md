# Deploy Demo to AI-Agency Repository

## Quick Deploy Steps

Run these commands in your terminal to add the demo to your AI-Agency website:

```bash
# 1. Clone AI-Agency repo
cd ~/Desktop
git clone https://github.com/abelcuskelly/AI-Agency.git

# 2. Copy the demo file
cp "Work/messaging agent/demo.html" AI-Agency/demo.html

# 3. Commit and push
cd AI-Agency
git add demo.html
git commit -m "Add AI agent interactive demo page"
git push origin main
```

## Result

After deployment, the demo will be live at:
**https://abelcuskelly.github.io/AI-Agency/demo.html**

## Add Link to Main Website

Edit `AI-Agency/index.html` and add a "Try Demo" button in the hero section:

```html
<a href="demo.html" class="cta-button">
    🚀 Try Live Demo
</a>
```

## Verify

Visit the demo:
- https://abelcuskelly.github.io/AI-Agency/demo.html

The demo showcases:
- 4 realistic conversation scenarios
- Interactive chat interface
- Agent capabilities display
- Performance metrics
- Fully responsive design
