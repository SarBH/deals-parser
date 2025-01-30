import os
import logging
from typing import Dict, Optional
from pyairtable import Table
from fuzzywuzzy import fuzz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AirtableManager:
    def __init__(self, api_key: str, base_id: str):
        self.api_key = api_key
        self.base_id = base_id
        
        # Initialize tables
        self.deals_table = Table(api_key, base_id, "Deals")
        self.properties_table = Table(api_key, base_id, "Properties")

        self.all_properties = self.properties_table.all()

    def create_deal(self, data: Dict) -> str:
        """Create a new deal record in Airtable"""
        try:
            # Format data for Airtable
            record = {
                "Address": data["street_address"],
                # "City": data["city"],
                # "State": data["state"],
                # "Zip": data["zip_code"],
                "Asking Price": float(data["price"].replace(",", "")),
                "Beds": int(data["bedrooms"]) if data["bedrooms"] else None,
                "Baths": float(data["bathrooms"]) if data["bathrooms"] else None,
                "MLS SF": float(data["sqft"].replace(",", "")) if data["sqft"] else 0,
                "Stage": "1-New",
                "Listing Images": data["image_urls"],
                "URL": data["listing_url"],
            }
            
            # Create the record
            created_record = self.deals_table.create(record)
            
            # Try to link to existing property
            property_record = self._find_matching_property(data["street_address"])
            if property_record:
                self.deals_table.update(created_record["id"], {
                    "Property": [property_record["id"]]
                })
            
            return created_record["id"]
            
        except Exception as e:
            logger.error(f"Error creating deal record: {str(e)}", exc_info=True)
            logger.info("Record data: %s", record)
            raise

    def update_deal_price(self, data: Dict):
        """Update deal record with new price"""
        try:
            # Find the deal record
            address = data["street_address"]
            formula = f"FIND('{address}', {{Address}}) > 0"
            records = self.deals_table.all(formula=formula)
            
            if not records:
                logger.warning(f"No deal found for address: {address}")
                return
            
            # Get the most recent record if multiple exist
            record = sorted(records, key=lambda x: x["createdTime"], reverse=True)[0]
            
            # Update the record
            new_price = float(data["price"].replace(",", ""))
            price_change = float(data["price_change"].replace(",", ""))
            
            updates = {
                "List Price": new_price,
                "Price Changes": f"Reduced by ${price_change:,.2f} on {data['timestamp']}"
            }
            
            # Append to price history if field exists
            if "Price History" in record["fields"]:
                updates["Price History"] = f"{record['fields']['Price History']}\n${new_price:,.2f} on {data['timestamp']}"
            else:
                updates["Price History"] = f"${new_price:,.2f} on {data['timestamp']}"
            
            self.deals_table.update(record["id"], updates)
            
        except Exception as e:
            logger.error(f"Error updating deal price: {str(e)}", exc_info=True)
            raise

    def _find_matching_property(self, address: str) -> Optional[Dict]:
        """Find matching property record using fuzzy string matching"""
        try:
            
            
            best_match = None
            best_ratio = 0
            
            for prop in self.all_properties:
                if "Address" not in prop["fields"]:
                    continue
                if prop["fields"]["Address"] is None:
                    raise ValueError("Property address is None")
                
                # Calculate similarity ratio
                ratio = fuzz.ratio(
                    address.lower(),
                    prop["fields"]["Address"].lower()
                )
                
                # Update best match if this is better
                if ratio > best_ratio and ratio >= 90:  # Minimum 90% match required
                    best_ratio = ratio
                    best_match = prop
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding matching property: {str(e)}", exc_info=True)
            return None

    def get_deal(self, deal_id: str) -> Optional[Dict]:
        """Get a deal record by ID"""
        try:
            return self.deals_table.get(deal_id)
        except Exception as e:
            logger.error(f"Error getting deal: {str(e)}", exc_info=True)
            return None