# Deals Parser

A Python application that monitors email alerts from real estate websites (Redfin, Zillow) and automatically creates/updates records in Airtable.

## Features

- Monitors Gmail inbox for real estate alerts
- Parses emails using customizable templates
- Creates new deal records in Airtable for new listings
- Updates existing deals when prices change
- Links deals to existing property records using fuzzy address matching
- Maintains a log of processed emails to avoid duplicates

## Setup

### Local Development

1. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
.\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file:
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required environment variables:
- `GMAIL_APP_PASSWORD`: App password for Gmail account
- `AIRTABLE_API_KEY`: Your Airtable API key

4. Create config.json (will be created automatically on first run):
```json
{
  "email": {
    "address": "asddealdump@gmail.com",
    "check_interval_minutes": 15
  },
  "airtable": {
    "base_id": "ASD Property Data",
    "deals_table": "Deals",
    "properties_table": "Properties"
  },
  "templates_dir": "templates",
  "processed_emails_log": "processed_emails.json"
}
```

### GitHub Actions Deployment

1. Fork this repository

2. Set up repository secrets:
   - Go to your repository's Settings > Secrets and variables > Actions
   - Add the following secrets:
     * `GMAIL_APP_PASSWORD`: Your Gmail app password
     * `AIRTABLE_API_KEY`: Your Airtable API key

3. The GitHub Action will:
   - Run every 15 minutes automatically
   - Can be triggered manually from the Actions tab
   - Store processed emails log as an artifact
   - Use the secrets instead of .env file

## Prerequisites Setup

### Gmail Setup
1. Create a Gmail account or use an existing one
2. Enable 2-factor authentication
3. Generate an App Password:
   - Go to Google Account settings
   - Security > 2-Step Verification > App passwords
   - Select "Mail" and your device
   - Copy the generated password

### Airtable Setup
1. Create a base with two tables: "Deals" and "Properties"
2. Generate an API key:
   - Go to https://airtable.com/account
   - Under API section, generate a new key
   - Copy the API key

## Usage

### Local Development

Run the configuration test:
```bash
python test_config.py
```

Run the script manually:
```bash
python main.py
```

### GitHub Actions

The workflow will run automatically every 15 minutes, but you can also:
1. Go to the Actions tab in your repository
2. Select "Process Real Estate Deals" workflow
3. Click "Run workflow"

## Email Templates

The application uses JSON templates to parse different types of real estate alert emails. Templates are stored in the `templates` directory.

### Template Structure

```json
{
  "name": "template_name",
  "trigger_pattern": "regex to identify email type",
  "patterns": {
    "trigger": "new listing|price drop",
    "street_address": "regex pattern",
    "city": "regex pattern",
    "state": "regex pattern",
    "zip_code": "regex pattern",
    "price": "regex pattern",
    "bedrooms": "regex pattern",
    "bathrooms": "regex pattern",
    "sqft": "regex pattern",
    "image_urls": "regex pattern"
  }
}
```

Two templates are included:
- redfin_new_listing.json - For parsing new listing alerts from Redfin
- zillow_price_change.json - For parsing price change alerts from Zillow

## Airtable Structure

### Deals Table
- Address (Text)
- City (Text)
- State (Text)
- Zip (Text)
- List Price (Number)
- Bedrooms (Number)
- Bathrooms (Number)
- Square Feet (Number)
- Stage (Single Select)
- Images (Multiple Attachments)
- Listing Date (Date)
- Price Changes (Text)
- Price History (Text)
- Property (Link to Properties table)

### Properties Table
- Address (Text)
- Other fields as needed for your property database

## Error Handling

- All errors are logged with timestamps and stack traces
- The script will continue running even if individual emails fail to process
- Failed emails will be retried on the next run
- Email IDs are only marked as processed after successful processing

## Contributing

Feel free to submit issues and enhancement requests!

## Deactivating Virtual Environment

When you're done working with the project, you can deactivate the virtual environment:
```bash
deactivate