# Information Gathering Approaches for Camp Data

This document summarizes three different approaches for gathering and extracting camp information from various sources.

## 1. Direct Info Extraction Through Prompts

### Overview
This approach uses direct prompting to extract structured information from unstructured data. The prompt in `prompts.txt` specifies exactly what information needs to be extracted and how it should be formatted.

### Implementation Details
- **Source File**: `prompts.txt`
- **Approach**: Asks an AI assistant to scan and read provided pages/URLs
- **Output Format**: Structured data in spreadsheet format
- **Fields Extracted**: Organization, Camp, Name, Start Date, End Date, Days, Start Time, End Time, Location, Age Range, Grade Range, Price, Description, email, contact information

### Advantages
- Simple implementation requiring minimal technical setup
- Flexible enough to handle varied document formats
- Can work directly with human-readable documents

### Limitations
- May have inconsistent formatting in the output
- Requires manual review for accuracy

## 2. Web Scraping

### Overview
This approach uses Selenium to programmatically navigate websites and extract camp information directly from web pages. The script in `web_scrape.py` specifically targets Lifetime Fitness camp pages.

### Implementation Details
- **Source File**: `web_scrape.py`
- **Technology Used**: Selenium, Python, Pandas
- **Fields Extracted**: Organization, Camp Name, Week, Days, Start Time, End Time, Location, Age Range, Grade Range, Price, Description, Email, Contact

### Key Features
- **Automated Navigation**: Clicks through "More Details" buttons to access additional information
- **Robust Error Handling**: Includes retries, timeouts, and exception handling
- **Data Processing**: Formats and standardizes extracted data

### Advantages
- Fully automated extraction without manual intervention
- Can handle dynamic content that requires interaction
- Capable of processing multiple entries efficiently
- Provides structured output ready for database import

### Limitations
- Highly site-specific implementation
- Requires maintenance when site structure changes
- More complex setup requiring ChromeDriver and dependencies

## 3. API-Based Data Extraction

### Overview
This approach leverages Google's Gemini API to extract structured data from image-based documents. The script in `info_extract.py` demonstrates using AI vision capabilities to parse tennis camp flyers.

### Implementation Details
- **Source File**: `info_extract.py`
- **Technology Used**: Google Gemini API, Python
- **Input Type**: Image files (PNG) containing camp information
- **Fields Extracted**: Similar to the other approaches, focusing on camp details

### Key Features
- **Image Processing**: Can extract text and structured data from images
- **API Integration**: Uses Google's Gemini model for advanced AI processing
- **Output Formatting**: Processes AI response into structured CSV format
- **Optional Parsing**: Includes functionality to further process data into JSON

### Advantages
- Can extract information from non-text sources (images, PDFs, etc.)
- Leverages specialized AI models for better accuracy with visual inputs
- Suitable for processing printed materials and marketing collateral

### Limitations
- Dependent on external API availability and costs
- Requires API key and authentication setup
- May have usage limits or rate restrictions

## Comparative Analysis

| Aspect | Direct Prompting | Web Scraping | API-Based Extraction |
|--------|-----------------|--------------|----------------------|
| Technical Complexity | Low | High | Medium |
| Setup Requirements | Minimal | Extensive | Moderate |
| Maintenance Needs | Low | High | Medium |
| Source Flexibility | High | Low | High |
| Automation Level | Semi-automated | Fully automated | Fully automated |
| Cost | Depends on AI service | Server/hosting costs | API usage costs |
| Scalability | Limited | High | High |

