# Deploy Demo to Your Website

## Quick Deploy Steps

Run these commands in your terminal to add the demo to your website:

```bash
# 1. Clone your website repository
cd ~/Desktop
git clone https://github.com/Company_Github_Repository/Company_Website.git

# 2. Copy the demo file
cp /path/to/messaging-agent/demo.html Company_Website/demo.html

# 3. Commit and push
cd Company_Website
git add demo.html
git commit -m "Add AI agent interactive demo page"
git push origin main
```

## Result

After deployment, the demo will be live at:
**https://company.github.io/demo.html**

## Add Link to Main Website

Edit `index.html` and add a "Try Demo" button in your hero or CTA section:

```html
<a href="demo.html" class="cta-button">
    🚀 Try Live Demo
</a>
```

## Verify

Visit the demo:
- https://company.github.io/demo.html

The demo showcases:
- 4 realistic conversation scenarios
- Interactive chat interface
- Agent capabilities display
- Performance metrics
- Fully responsive design
