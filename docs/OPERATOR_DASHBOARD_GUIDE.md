# SpendSense Operator Dashboard - Usage Guide

**Version**: 1.0  
**Last Updated**: January 2025  
**Purpose**: Guide for operators using the SpendSense Streamlit dashboard

---

## 🚀 Quick Start

### Starting the Dashboard

```bash
# Ensure Docker container is running
make up

# Access container shell
make shell

# Start Streamlit dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

# Dashboard will be available at: http://localhost:8501
```

**Note**: The dashboard runs inside the Docker container. Access it from your host machine's browser at `http://localhost:8501`.

---

## 📊 Dashboard Overview

The SpendSense Operator Dashboard provides 7 main views:

1. **User View** - End-user interface for viewing personalized recommendations
2. **System Overview** - High-level system health and metrics
3. **User Analytics** - Detailed user insights and persona distribution
4. **Recommendation Engine** - Recommendation management and approval queue
5. **Data Quality** - Data quality monitoring and validation
6. **Performance Metrics** - System performance and fairness metrics
7. **System Logs** - System activity logs

---

## 🎯 Page-by-Page Guide

### 1. User View

**Purpose**: End-user interface for viewing personalized financial recommendations

**How to Use**:
1. Navigate to "User View" from the sidebar
2. Enter a user ID (e.g., `user_001`)
3. Click "🔍 Load My Profile"
4. View the user's:
   - **Persona Card**: Shows assigned persona with icon, description, and matched criteria
   - **Recommendations**: Personalized recommendations with:
     - Title and description
     - "Why this matters" rationale (explains why the recommendation was made)
     - Reading time and content type
     - "Learn More" button

**Key Features**:
- User-friendly language (not technical)
- Clear persona explanation
- Actionable recommendations with rationales
- Recommendations automatically marked as viewed when displayed

**Use Cases**:
- Demo the end-user experience
- Verify recommendations are user-friendly
- Check that rationales are clear and personalized

---

### 2. System Overview

**Purpose**: High-level system health monitoring

**Key Metrics Displayed**:
- **Total Users**: Number of users in the system
- **Signal Coverage**: Percentage of users with computed signals
- **Avg Data Quality**: Average data quality score (0.0-1.0)
- **24h Recommendations**: Recommendations generated in last 24 hours

**System Status Cards**:
- **Recommendation Engine**: Shows if engine is active and serving users
- **Signal Detection**: Shows if signal detection is processing users

**Sidebar Quick Stats**:
- Real-time system health indicator (✅ Healthy / ❌ Issues)
- Quick stats: Users, Signal Coverage, Avg Data Quality, Recent Recs
- Last refresh timestamp

**How to Use**:
- Check system health at a glance
- Monitor key metrics for anomalies
- Use "🔄 Refresh Data" button to update metrics
- Enable "Auto-refresh (30s)" for continuous monitoring

**Use Cases**:
- Daily health checks
- Monitoring system status
- Quick metric overview

---

### 3. User Analytics

**Purpose**: Detailed user insights and analytics

**Sections**:

#### User Overview
- Total Users count
- Consent Rate percentage
- Users with Good Signals percentage
- Users with Recommendations count and percentage

#### Persona Distribution
- Pie chart showing persona breakdown
- Table with persona counts and percentages
- Shows all 5 personas: High Utilization, Variable Income, Subscription-Heavy, Savings Builder, Fee Fighter

#### Data Quality Analysis
- Histogram of data quality scores
- Quality metrics: average, median, low/high quality counts
- Helps identify users needing more transaction data

#### Signal Insights
- Credit utilization distribution (if data available)
- Subscription count distribution
- Other behavioral signal distributions

#### User Details
- Searchable user list table
- Filters:
  - Quality filter (All / Good / Poor)
  - Show count selector (10 / 25 / 50 / 100)
- Displays: User ID, Persona, Data Quality, Signal Coverage, Recommendation Count

**How to Use**:
- Analyze persona distribution to understand user base
- Identify users with poor data quality
- Search for specific users
- Filter by data quality to focus on high-quality users

**Use Cases**:
- Understanding user base composition
- Identifying data quality issues
- Finding specific users for review
- Analyzing behavioral patterns

---

### 4. Recommendation Engine

**Purpose**: Recommendation management and approval workflow

**Features**:
- **Approval Queue**: View pending recommendations awaiting approval
- **Recent Recommendations**: View recently generated recommendations
- **Recommendation Details**: 
  - User ID and persona
  - Content title and description
  - Rationale explaining why recommendation was made
  - Approval status
  - Created timestamp

**How to Use**:
1. View recommendations in approval queue
2. Review rationale for each recommendation
3. Approve or reject recommendations (if approval workflow implemented)
4. Filter by status (Pending / Approved / Rejected)
5. Search by user ID or content ID

**Use Cases**:
- Review recommendations before delivery
- Quality assurance of recommendation rationales
- Approval workflow management
- Monitoring recommendation generation

---

### 5. Data Quality

**Purpose**: Monitor data quality across users

**Features**:
- **Data Quality Distribution**: Histogram showing quality score distribution
- **Quality Metrics**: 
  - Average data quality score
  - Median data quality score
  - Users with low quality (< 0.5)
  - Users with high quality (>= 0.8)
- **Quality Breakdown**: 
  - Users by quality tier
  - Common quality issues
- **User List**: Filterable list of users by quality score

**How to Use**:
- Monitor overall data quality trends
- Identify users with insufficient data
- Filter users by quality tier
- Investigate quality issues

**Use Cases**:
- Data quality monitoring
- Identifying users needing more transaction data
- Quality assurance
- Data collection planning

---

### 6. Performance Metrics

**Purpose**: System performance monitoring and fairness metrics

**Sections**:

#### Performance Metrics
- **P95 Compute Time**: 95th percentile computation time (target: <500ms)
- **Error Rate**: Percentage of users with computation errors (target: <20%)
- **Avg Response Time**: Average API response time
- **Total Requests**: Total API requests processed

#### Performance Breakdown
- Compute time distribution chart
- Error rate trends (when historical data available)
- API endpoint performance table

#### Recommendation Relevance
- Average relevance score
- High relevance count (>= 0.8)
- Low relevance count (< 0.5)
- Relevance distribution chart

#### Fairness Metrics ⚖️
- **Demographic Parity**: Coefficient of variation (lower is better)
- **Recommendation Rates by Group**: Shows recommendation rates per demographic group
- **Disparities Detected**: Flags groups with >10% difference from average
- **Parity Status**: "good" (CV < 10%) or "needs_review" (CV >= 10%)

**Note**: Fairness metrics require demographic data in the users table. If not available, shows framework message with implementation notes.

**How to Use**:
- Monitor system performance against targets
- Check recommendation relevance scores
- Review fairness metrics for demographic parity
- Investigate performance bottlenecks
- Monitor error rates

**Use Cases**:
- Performance monitoring
- Fairness auditing
- Quality assurance
- System optimization

---

### 7. System Logs

**Purpose**: View system activity logs

**Features**:
- Recent system logs
- Log filtering by level (INFO / WARNING / ERROR)
- Search functionality
- Log export (if implemented)

**How to Use**:
- Monitor system activity
- Debug issues
- Review error logs
- Track system events

**Use Cases**:
- Troubleshooting
- System monitoring
- Error investigation
- Activity auditing

---

## ⚙️ Dashboard Settings

### Sidebar Controls

**Database Path**:
- Default: `db/spend_sense.db`
- Change to use a different database file
- Updates automatically when changed

**Auto-refresh**:
- Checkbox to enable auto-refresh every 30 seconds
- Useful for monitoring real-time changes
- Disable to reduce resource usage

**Refresh Data Button**:
- Manual refresh of all dashboard data
- Updates all metrics and displays
- Shows last refresh timestamp in sidebar

**🔧 Compute Signals Button**:
- **What it does**: Computes behavioral signals for all users (credit utilization, subscriptions, savings, income patterns)
- **When to use**: When users have gray icons (no personas assigned) or when you need to recompute signals
- **What to expect**:
  - Spinner appears: "Computing signals for all users... This may take a few minutes"
  - Takes 1-2 minutes for 50 users
  - On success: "✅ Signal computation complete for X users!" with next steps
  - Page auto-refreshes after completion
- **After completion**:
  - User personas will appear (colored icons instead of gray in User View)
  - You can now view personalized recommendations
  - To generate recommendations: The system will auto-generate them, or you can wait for the initialization script to complete

---

## 🔍 Common Tasks

### Task 1: Check System Health

1. Navigate to "System Overview"
2. Check key metrics:
   - Signal Coverage should be > 0%
   - Avg Data Quality should be > 0.5
   - 24h Recommendations should be > 0 (if system is active)
3. Verify system status cards show "✅ Active"
4. Check sidebar for "✅ System Healthy" indicator

### Task 2: Find Users with Poor Data Quality

1. Navigate to "Data Quality"
2. Review quality distribution histogram
3. Filter user list by "Poor" quality
4. Review users with quality < 0.5
5. Note which users need more transaction data

### Task 3: Review Persona Distribution

1. Navigate to "User Analytics"
2. Scroll to "Persona Distribution" section
3. Review pie chart and table
4. Verify all 5 personas are represented (if enough users)
5. Check for unexpected persona concentrations

### Task 4: Check Recommendation Quality

1. Navigate to "Recommendation Engine"
2. Review approval queue
3. Check rationales for clarity and personalization
4. Verify recommendations match user personas
5. Approve or reject as needed

### Task 5: Monitor Performance

1. Navigate to "Performance Metrics"
2. Check P95 Compute Time (should be < 500ms)
3. Check Error Rate (should be < 20%)
4. Review relevance scores (should be > 0.5 average)
5. Check fairness metrics for parity issues

### Task 6: View End-User Experience

1. Navigate to "User View"
2. Enter a test user ID (e.g., `user_001`)
3. Click "🔍 Load My Profile"
4. Review persona card and recommendations
5. Verify user-friendly language and clear rationales

---

## 🐛 Troubleshooting

### Dashboard Won't Start

**Issue**: `streamlit run` command fails

**Solutions**:
- Ensure Docker container is running: `make up`
- Check you're in the container shell: `make shell`
- Verify Python dependencies: `pip list | grep streamlit`
- Check for port conflicts (8501 already in use)

### No Data Displayed

**Issue**: Dashboard shows 0 users or empty tables

**Solutions**:
- Verify database path is correct (check sidebar)
- Ensure database is initialized: `python -c "from src.db.connection import initialize_db; initialize_db()"`
- Check if data is loaded: `sqlite3 db/spend_sense.db "SELECT COUNT(*) FROM users"`
- Generate test data if needed: `python -m src.ingest.data_generator --users 50`

### Metrics Not Updating

**Issue**: Metrics show stale data

**Solutions**:
- Click "🔄 Refresh Data" button
- Check database path is correct
- Verify database file exists and is accessible
- Check for database lock errors in logs

### Performance Issues

**Issue**: Dashboard is slow or unresponsive

**Solutions**:
- Disable auto-refresh if enabled
- Reduce number of users in database
- Check database file size (SQLite can be slow with large files)
- Consider using a smaller test database

### Fairness Metrics Not Showing

**Issue**: Fairness metrics show "framework" message

**Solutions**:
- This is expected if demographic data is not in users table
- To enable fairness metrics, add demographic columns to users table:
  - `demographic_group TEXT`
  - Or `age_range TEXT`, `income_level TEXT`, etc.
- See `src/evaluation/metrics.py` for implementation details

---

## 📝 Best Practices

1. **Regular Health Checks**: Check System Overview daily
2. **Monitor Data Quality**: Review Data Quality page weekly
3. **Review Recommendations**: Check Recommendation Engine regularly for quality
4. **Performance Monitoring**: Monitor Performance Metrics for degradation
5. **Fairness Auditing**: Review Fairness Metrics periodically
6. **User Experience**: Test User View with real user IDs to verify UX
7. **Log Review**: Check System Logs when investigating issues

---

## 🔗 Related Documentation

- **API Documentation**: See `README.md` for API endpoint details
- **Testing Guide**: See `docs/Testing-Manual.md` for testing procedures
- **Architecture**: See `docs/Architecture-Guide.md` for system architecture
- **Decision Log**: See `docs/DECISION_LOG.md` for architectural decisions

---

## 📞 Support

For issues or questions:
1. Check System Logs page for error messages
2. Review troubleshooting section above
3. Check `docs/Testing-Manual.md` for validation steps
4. Review code comments in `src/ui/` directory

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Maintained By**: Development Team

