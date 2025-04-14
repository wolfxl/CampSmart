from PIL import Image
from google import genai
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Load the image of the tennis camp flyer
#image = Image.open("sources/lakes_tennis_camps_2025.png") 
image1= Image.open("sources/Sky lark/info1.png")
image2= Image.open("sources/Sky lark/info2.png")
image3= Image.open("sources/Sky lark/info3.png")

# Create the prompt to extract structured data
extraction_prompt = """
Please scan and read the tennis camp flyer in this image, and extract the information in CSV format with columns: 
Organization, Camp Name, Start Date, End Date, Days, Start Time, End Time, Location, Age Range, Grade Range, 
Price, Description, Email, Contact Information.

Note that each row should contain only one camp. Format your response as a valid CSV string that can be directly parsed.
"""

# Send the request to Gemini
response = client.models.generate_content(
    model="gemini-2.5-pro-exp-03-25",  # Using experimental version with free tier
    contents=[
        image1,  # The flyer image
        image2,  # The flyer image
        image3,  # The flyer image
        extraction_prompt  # Our detailed extraction request
    ]
)

# Get the response text (CSV data)
csv_data = response.text

# Remove the ```csv line if it exists
if csv_data.startswith("```csv"):
    csv_data = csv_data.replace("```csv\n", "", 1)
elif csv_data.startswith("```"):
    csv_data = csv_data.replace("```\n", "", 1)

# Save the CSV data to a file
with open("lakes_tennis_camps_2025.csv", "w") as f:
    f.write(csv_data)

print("CSV data extracted and saved to lakes_tennis_camps_2025.csv")

# Optional: Parse the CSV into a more workable format
# This could be useful if you want to process the data further
import csv
from io import StringIO

csv_reader = csv.DictReader(StringIO(csv_data))
camps_data = list(csv_reader)

# Example: Print the first camp entry as JSON
if camps_data:
    print("\nFirst camp entry:")
    print(json.dumps(camps_data[0], indent=2))