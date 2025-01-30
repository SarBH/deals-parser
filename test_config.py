#!/usr/bin/env python3
import os
import json
import imaplib
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def test_gmail_connection():
    """Test Gmail connection using app password"""
    print("\nTesting Gmail connection...")
    
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not password:
        print("❌ GMAIL_APP_PASSWORD not found in environment variables or .env file")
        return False
    
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login("asddealdump@gmail.com", password)
        print("✅ Successfully connected to Gmail")
        mail.logout()
        return True
    except Exception as e:
        print(f"❌ Gmail connection failed: {str(e)}")
        return False

def test_airtable_connection():
    """Test Airtable connection and table access"""
    print("\nTesting Airtable connection...")
    
    api_key = os.getenv("AIRTABLE_API_KEY")
    if not api_key:
        print("❌ AIRTABLE_API_KEY not found in environment variables or .env file")
        return False
    
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    except json.JSONDecodeError:
        print("❌ config.json is not valid JSON")
        return False
    
    if "airtable" not in config:
        print("❌ Airtable configuration not found in config.json")
        return False
    
    airtable_config = config["airtable"]
    
    try:
        # Test Deals table
        api = Api(api_key)
        
        deals_table = api.table(
            airtable_config["base_id"],
            airtable_config["deals_table"]
        )
        deals_table.all(max_records=1)
        print("✅ Successfully connected to Deals table")
        
        # Test Properties table
        properties_table = api.table(
            airtable_config["base_id"],
            airtable_config["properties_table"]
        )
        properties_table.all(max_records=1)
        print("✅ Successfully connected to Properties table")
        
        return True
    except Exception as e:
        print(f"❌ Airtable connection failed: {str(e)}")
        return False

def test_templates():
    """Test that template files exist and are valid JSON"""
    print("\nTesting templates...")
    
    template_files = [
        "redfin_new_listing.json",
        "zillow_price_change.json"
    ]
    
    all_valid = True
    for filename in template_files:
        path = os.path.join("templates", filename)
        try:
            with open(path) as f:
                json.load(f)
            print(f"✅ Successfully loaded {filename}")
        except FileNotFoundError:
            print(f"❌ Template file not found: {filename}")
            all_valid = False
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in template: {filename}")
            all_valid = False
    
    return all_valid

def test_env_variables():
    """Test that all required environment variables are set"""
    print("\nTesting environment variables...")
    
    required_vars = {
        "GMAIL_APP_PASSWORD": "Gmail App Password",
        "AIRTABLE_API_KEY": "Airtable API Key"
    }
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {description} is set")
        else:
            print(f"❌ {description} is not set")
            all_set = False
    
    return all_set

def main():
    print("Running configuration tests...")
    print("==============================")
    
    env_ok = test_env_variables()
    gmail_ok = test_gmail_connection()
    airtable_ok = test_airtable_connection()
    templates_ok = test_templates()
    
    print("\nTest Summary")
    print("============")
    print(f"Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"Gmail Connection: {'✅' if gmail_ok else '❌'}")
    print(f"Airtable Connection: {'✅' if airtable_ok else '❌'}")
    print(f"Templates: {'✅' if templates_ok else '❌'}")
    
    if all([env_ok, gmail_ok, airtable_ok, templates_ok]):
        print("\n✅ All tests passed! The script is ready to run.")
    else:
        print("\n❌ Some tests failed. Please fix the issues above before running the main script.")

if __name__ == "__main__":
    main()