# Jobcan Automation

This script automates the process of clicking "Clock Out" (退勤) at 12:00 and "Clock In" (出勤) at 13:00 on Jobcan.

## Setup Credentials

1.  **Configure Credentials**:
    -   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Open `.env` and fill in your Jobcan email and password.

## Usage (Docker - Recommended)

This is the best way to keep the bot running in the background.

1.  **Build and Start**:
    ```bash
    docker-compose up -d --build
    ```
    (The `-d` flag runs it in the background).

2.  **Check Logs**:
    ```bash
    docker-compose logs -f
    ```

3.  **Stop**:
    ```bash
    docker-compose down
    ```

## Usage (Local Python)

If you prefer to run it manually in your terminal:

1.  **Install Dependencies**:
    ```bash
    pip3 install -r requirements.txt
    ```

2.  **Run**:
    ```bash
    python3 jobcan_bot.py
    ```
    *Note: You must keep the terminal window open.*

## Testing

To test if the login and button clicking works immediately (without waiting for 12:00/13:00), you can uncomment the lines at the bottom of `jobcan_bot.py`:

```python
# job_clock_out()
# job_clock_in()
```
