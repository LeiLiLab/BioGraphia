# BioGraphia

You can try BioGraphia on [link](https://biographia.share.zrok.io/#/). We disabled login for the demo version.

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

## Creating a zrok tunnel
To create your own zrok tunnel, use the following commands:
1. Create a zrok account to get your account token.
2. Download zrok through this [link](https://docs.zrok.io/docs/getting-started/?_gl=1*28k332*_gcl_au*MTEyMzMyNDAyMy4xNzQzMTMzNDM0*_ga*MTAwMjkwNDA3NC4xNzQzMTMzNDM0*_ga_V2KMEXWJ10*MTc0Mzk5MDA3OS44LjAuMTc0Mzk5MDA3OS42MC4wLjA.#installing-the-zrok-command).
3. Enable zrok for your account.
```
zrok enable <your_account_token>
```
4. Reserve a public share token named <unique_name>
```
zrok reserve public <your_local_frontend_url> --unique-name <unique_name>
```
5. Share the reserved token
```
zrok share reserved <unique_name>
```
6. Now you should be able to visit the site using <unique_name>.share.zrok.io.

This project is licensed under the Apache 2.0 License.
