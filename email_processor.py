import os
import re
import email
import imaplib
import logging
from typing import Dict, List, Optional
from email.header import decode_header
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EmailProcessor:
    def __init__(self, email_address: str, templates: Dict):
        self.email_address = email_address
        self.templates = templates
        self.imap_server = "imap.gmail.com"
        
        # Get password from environment variable
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        if not self.password:
            raise ValueError("GMAIL_APP_PASSWORD not found in environment variables or .env file")

    def get_new_emails(self, processed_ids: List[str]) -> List[Dict]:
        """Fetch new emails from Gmail"""
        emails = []
        
        try:
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.password)
            mail.select("INBOX")
            
            # Search for all emails
            _, message_numbers = mail.search(None, "ALL")
            
            for num in message_numbers[0].split():
                # Fetch email message
                _, msg_data = mail.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)
                
                # Get email ID (Message-ID header)
                email_id = message["Message-ID"]
                
                # Skip if already processed
                if email_id in processed_ids:
                    continue
                
                # Extract subject
                subject = self._decode_header(message["subject"])
                
                # Extract body
                body = self._get_email_body(message)
                
                emails.append({
                    "id": email_id,
                    "subject": subject,
                    "body": body,
                    "date": message["date"]
                })
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error("Error fetching emails", exc_info=True)
            raise
        
        return emails

    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        decoded_header = decode_header(header)[0]
        if isinstance(decoded_header[0], bytes):
            return decoded_header[0].decode(decoded_header[1] or 'utf-8')
        return decoded_header[0]

    def _get_email_body(self, message) -> str:
        """Extract email body text"""
        body = ""
        
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        continue
        else:
            body = message.get_payload(decode=True).decode()
        
        return body

    def parse_email(self, email_data: Dict) -> Optional[Dict]:
        """Parse email using templates"""
        for template in self.templates.values():
            # Check if email matches template's trigger pattern
            if re.search(template["trigger_pattern"], email_data["subject"], re.IGNORECASE):
                return self._extract_data(email_data, template)
        
        return None

    def _extract_data(self, email_data: Dict, template: Dict) -> Dict:
        """Extract data from email using template patterns"""
        result = {
            "trigger": template["patterns"]["trigger"],
            "image_urls": []
        }
        
        # Combine subject and body for searching
        text = f"{email_data['subject']}\n{email_data['body']}"
        
        # Extract each field using patterns
        for field, pattern in template["patterns"].items():
            if field in ["trigger", "image_urls", "complete_address", "listing_url"]:
                continue
                
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result[field] = match.group(1)
            else:
                result[field] = None

        # Extract listing URL
        match = re.search(template["patterns"]["listing_url"], text, re.IGNORECASE | re.MULTILINE)
        result["listing_url"] = match.group(0) if match else None

        # Extract addresses
        # Apply regex
        match = re.search(template["patterns"]["complete_address"], text, re.IGNORECASE | re.MULTILINE)
        result["street_address"] = match.group(1) if match else None
        result["city"] = match.group(2) if match else None
        result["state"] = match.group(3) if match else None
        result["zip_code"] = match.group(4) if match else None

        # Extract image URLs
        image_urls = re.findall(template["patterns"]["image_urls"], text)
        result["image_urls"] = list(set(image_urls))  # Remove duplicates
        
        
        return result