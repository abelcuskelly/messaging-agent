# Jupyter Notebooks - Qwen Messaging Agent

This directory contains Jupyter notebooks for interactive development, analysis, and experimentation with the Qwen Messaging Agent.

## 📁 Directory Structure

```
notebooks/
├── README.md                    # This file
├── requirements.txt              # Jupyter-specific dependencies
├── setup_jupyter.py            # Setup script
├── .env.template               # Environment variables template
├── templates/                  # Notebook templates
│   └── 01_Quick_Start.ipynb    # Getting started guide
├── analysis/                   # Data analysis notebooks
│   └── 02_Data_Analysis.ipynb  # Performance analysis
├── experiments/                # Model experimentation
│   └── 03_Model_Experiments.ipynb # A/B testing and evaluation
└── visualization/              # Interactive dashboards
    └── 04_Interactive_Dashboard.ipynb # Real-time monitoring
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Navigate to notebooks directory
cd notebooks

# Run setup script
python setup_jupyter.py

# Copy environment template
cp .env.template .env
# Edit .env with your actual values
```

### 2. Start Jupyter Lab

```bash
# Start Jupyter Lab
jupyter lab

# Or start classic Jupyter Notebook
jupyter notebook
```

### 3. Select Kernel

When opening notebooks, select the **"Qwen Messaging Agent"** kernel.

## 📓 Available Notebooks

### Templates

- **`01_Quick_Start.ipynb`** - Introduction to the messaging agent system
  - Environment setup
  - Basic chat functionality
  - Tools and RAG usage
  - Troubleshooting guide

### Analysis

- **`02_Data_Analysis.ipynb`** - Performance and conversation analysis
  - Response time analysis
  - User engagement metrics
  - Error rate monitoring
  - Tool usage patterns

### Experiments

- **`03_Model_Experiments.ipynb`** - Model evaluation and testing
  - A/B testing framework
  - Quality assessment
  - Performance comparison
  - Hyperparameter optimization

### Visualization

- **`04_Interactive_Dashboard.ipynb`** - Real-time monitoring dashboards
  - Interactive charts and graphs
  - Real-time data visualization
  - Performance monitoring
  - Alert systems

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Google Cloud Configuration
PROJECT_ID=your-project-id
REGION=us-central1
ENDPOINT_ID=your-endpoint-id

# BigQuery Configuration
DATASET_ID=messaging_agent
TABLE_ID=conversations

# Storage Configuration
BUCKET_NAME=your-bucket-name

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Authentication
API_KEY=your-api-key
JWT_SECRET_KEY=your-jwt-secret

# Monitoring
WANDB_PROJECT=qwen-messaging-agent
WANDB_API_KEY=your-wandb-key
```

### Dependencies

The `requirements.txt` file includes:

- **Jupyter**: Core notebook environment
- **Data Science**: pandas, numpy, matplotlib, seaborn, plotly
- **Machine Learning**: scikit-learn, transformers, torch
- **Google Cloud**: aiplatform, storage, bigquery
- **Visualization**: ipywidgets, ipympl, bqplot, altair
- **Utilities**: tqdm, rich, python-dotenv

## 📊 Features

### Interactive Development

- **Real-time Model Testing**: Test different configurations interactively
- **Data Exploration**: Explore conversation data with pandas and plotly
- **Performance Monitoring**: Visualize metrics and trends
- **A/B Testing**: Compare different model versions

### Data Analysis

- **Conversation Patterns**: Analyze user interaction patterns
- **Performance Metrics**: Response times, error rates, satisfaction scores
- **Tool Usage**: Track which tools are most effective
- **User Engagement**: Understand user behavior and preferences

### Visualization

- **Interactive Dashboards**: Real-time monitoring with plotly
- **Custom Charts**: Create custom visualizations for specific metrics
- **Export Capabilities**: Export charts and data for reports
- **Real-time Updates**: Live data updates for monitoring

## 🛠️ Usage Examples

### Basic Chat Testing

```python
# Initialize agent
agent = MessagingAgent(
    project_id=PROJECT_ID,
    region=REGION,
    endpoint_id=ENDPOINT_ID
)

# Test conversation
response = agent.chat("Hello! I need tickets for tonight's game.")
print(response)
```

### Data Analysis

```python
# Load conversation data
df = load_conversation_data(days_back=30)

# Analyze response times
avg_response_time = df['response_time_ms'].mean()
print(f"Average response time: {avg_response_time:.2f} ms")
```

### Model Evaluation

```python
# Evaluate model performance
results = evaluate_model_performance(endpoint_id, test_scenarios)

# View quality scores
for scenario in results['scenarios']:
    print(f"{scenario['scenario']}: {scenario['quality_scores']['overall_score']:.2f}")
```

### Interactive Dashboard

```python
# Create dashboard
fig = create_interactive_dashboard(days_back=7)

# Display interactive chart
fig.show()
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're using the correct kernel and have installed all dependencies
2. **Authentication**: Verify your Google Cloud credentials are set up correctly
3. **BigQuery Access**: Ensure you have the necessary BigQuery permissions
4. **Environment Variables**: Check that your `.env` file is properly configured

### Getting Help

- Check the main project README.md for detailed setup instructions
- Review the troubleshooting section in each notebook
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## 📈 Best Practices

### Notebook Organization

- **Clear Sections**: Use markdown cells to organize your work
- **Documentation**: Document your analysis and findings
- **Reproducibility**: Include all necessary imports and setup code
- **Version Control**: Commit notebooks to track changes

### Performance

- **Data Sampling**: Use sampling for large datasets during development
- **Caching**: Cache expensive computations when possible
- **Memory Management**: Clear large variables when not needed
- **Parallel Processing**: Use multiprocessing for large-scale analysis

### Collaboration

- **Clear Outputs**: Ensure notebook outputs are meaningful
- **Comments**: Add comments explaining complex logic
- **Sharing**: Export notebooks to HTML or PDF for sharing
- **Review**: Have team members review analysis notebooks

## 🚀 Advanced Features

### Custom Visualizations

Create custom visualizations for specific metrics:

```python
# Custom performance chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=response_times, mode='lines'))
fig.update_layout(title="Custom Performance Chart")
fig.show()
```

### Real-time Monitoring

Set up real-time monitoring with automatic updates:

```python
# Real-time dashboard with auto-refresh
def update_dashboard():
    fig = create_interactive_dashboard()
    fig.show()

# Schedule updates every 5 minutes
import schedule
schedule.every(5).minutes.do(update_dashboard)
```

### Export and Reporting

Export analysis results for reports:

```python
# Export to different formats
df.to_csv('analysis_results.csv')
fig.write_html('dashboard.html')
fig.write_image('chart.png')
```

## 📚 Additional Resources

- [Jupyter Documentation](https://jupyter.org/documentation)
- [Plotly Documentation](https://plotly.com/python/)
- [Google Cloud BigQuery](https://cloud.google.com/bigquery/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)

## 🤝 Contributing

When adding new notebooks:

1. Follow the existing naming convention
2. Include proper documentation and markdown cells
3. Add the notebook to this README
4. Test the notebook with sample data
5. Include troubleshooting information

## 📄 License

This project is part of the Qwen Messaging Agent system. See the main project LICENSE file for details.
