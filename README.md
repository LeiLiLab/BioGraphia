# PathwayAnno

## System Requirements

- Python 3.6 or higher
- Node.js 18 or higher
- npm or yarn package manager

## Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd PathwayAnno
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

The application can be started with a single command:

```
python start.py
```

This command will:
1. Start the Flask backend server
2. Start the Quasar frontend development server

### Backend

- The backend is a Flask application located at `src/server/app.py`
- It runs on `http://localhost:5000` by default
- Provides REST API endpoints for paper analysis and data management

### Frontend

- The frontend is built with Quasar Framework (Vue.js)
- It runs on `http://localhost:8888`

# Start of Selection
## License

This project is licensed under the Apache 2.0 License.