import os
import json
import pandas as pd
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcs_key.json"

BUCKET_NAME = "gemma3n-raw"
SESSIONS_PREFIX = "sessions/"

def process_sessions():
    """Read all session JSONs from GCS and create DataFrame"""
    
    # Get GCS client
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    
    # Get all JSON files
    blobs = bucket.list_blobs(prefix=SESSIONS_PREFIX)
    json_files = [blob for blob in blobs if blob.name.endswith('.json')]
    
    print(f"Found {len(json_files)} session files")
    
    # Read each JSON and flatten
    all_data = []
    for blob in json_files:
        try:
            content = blob.download_as_text()
            data = json.loads(content)
            
            # Flatten nested data
            flat_data = {**data}  # Copy all top-level fields
            
            # Flatten analysis_breakdown if exists
            if 'analysis_breakdown' in data:
                breakdown = data['analysis_breakdown']
                
                if 'density_stats' in breakdown:
                    for key, value in breakdown['density_stats'].items():
                        flat_data[f'density_{key.lower()}'] = value
                
                if 'motion_stats' in breakdown:
                    for key, value in breakdown['motion_stats'].items():
                        flat_data[f'motion_{key.lower()}'] = value
                
                if 'risk_levels' in breakdown:
                    for key, value in breakdown['risk_levels'].items():
                        flat_data[f'risk_{key.lower()}'] = value
                
                # Remove original nested field
                del flat_data['analysis_breakdown']
            
            all_data.append(flat_data)
            
        except Exception as e:
            print(f"Error processing {blob.name}: {e}")
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    print(f"Created DataFrame with {len(df)} rows")
    
    # Save to CSV
    df.to_csv("sessions_data.csv", index=False)
    print("Saved to sessions_data.csv")
    
    return df

if __name__ == "__main__":
    df = process_sessions()
    print(df.head())