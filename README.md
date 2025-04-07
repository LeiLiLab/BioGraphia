# BioGraphia

You can try BioGraphia on link. We disabled login for the demo version.

## Configuration
Create a .env file in the root directory and set the following variables:

### OpenAI Configuration
OPENAI_API_KEY= [YOUR_API_KEY_HERE]
OPENAI_ANALYSIS_MODEL=o1
OPENAI_JSON_MODEL=gpt-4o

### Server Configuration
VITE_SERVER_HOST=localhost
VITE_BACKEND_PORT=3000 # Backend Port
VITE_FRONTEND_PORT=9000 # Frontend Port

## Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd BioGraphia
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```
   npm install
   ```

## Running the Application

the application can be started with a single command:

```
python start.py
```

Run the application in standalone mode:

```
python start.py --standalone
```
this will restore the data every 5 minutes

This project is licensed under the Apache 2.0 License.