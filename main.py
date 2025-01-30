#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DealsParser:
    def __init__(self, config_path: str = "config.json"):
        # Load environment variables
        self.airtable_api_key = os.getenv("AIRTABLE_API_KEY")
        if not self.airtable_api_key:
            raise ValueError("AIRTABLE_API_KEY not found in environment variables or .env file")
            
        self.config = self._load_config(config_path)
        self.templates = self._load_templates()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        if not os.path.exists(config_path):
            default_config = {
                "email": {
                    "address": "<email_address>@gmail.com",
                    "check_interval_minutes": 15
                },
                "airtable": {
                    "base_id": "<replace with base ID>",
                    "deals_table": "<replace with table ID>",
                    "properties_table": "<replace with table ID>"
                },
                "templates_dir": "templates",
                "processed_emails_log": "processed_emails.json"
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
        
        with open(config_path) as f:
            return json.load(f)

    def _load_templates(self) -> Dict:
        """Load all templates from the templates directory"""
        templates = {}
        templates_dir = self.config["templates_dir"]
        
        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                with open(os.path.join(templates_dir, filename)) as f:
                    template = json.load(f)
                    templates[template["name"]] = template
        
        return templates

    def _load_processed_emails(self) -> List[str]:
        """Load list of already processed email IDs"""
        log_file = self.config["processed_emails_log"]
        if os.path.exists(log_file):
            with open(log_file) as f:
                return json.load(f)
        return []

    def _save_processed_email(self, email_id: str):
        """Save email ID to processed emails log"""
        processed = self._load_processed_emails()
        processed.append(email_id)
        
        with open(self.config["processed_emails_log"], 'w') as f:
            json.dump(processed, f)

    def process_new_emails(self):
        """Main function to process new emails"""
        from email_processor import EmailProcessor
        from airtable_manager import AirtableManager
        
        # Initialize components
        email_processor = EmailProcessor(
            self.config["email"]["address"],
            self.templates
        )
        
        airtable = AirtableManager(
            self.airtable_api_key,
            self.config["airtable"]["base_id"]
        )
        
        # Get list of processed emails
        processed_emails = self._load_processed_emails()
        
        # Get new emails
        new_emails = email_processor.get_new_emails(processed_emails)
        
        for email in new_emails:
            try:
                # Parse email using templates
                parsed_data = email_processor.parse_email(email)
                
                if parsed_data:
                    # Update Airtable
                    if parsed_data["trigger"] == "new listing":
                        airtable.create_deal(parsed_data)
                    elif parsed_data["trigger"] == "price drop":
                        airtable.update_deal_price(parsed_data)
                    
                    # Mark email as processed
                    self._save_processed_email(email["id"])
                    
                    logger.info(f"Successfully processed email: {email['subject']}")
                
            except Exception as e:
                logger.error(f"Error processing email: {email['subject']}", exc_info=True)
                logger.info("Email data: %s", parsed_data)

def main():
    parser = DealsParser()
    parser.process_new_emails()

if __name__ == "__main__":
    main()