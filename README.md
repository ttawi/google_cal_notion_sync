# google Calendar Notion Sync
A tool to sync google calendar events to notion that can be deployed through Docker.

# Local development

1. Install dependencies with
```
pip3 install -r requirements.txt
```

2. Register a Google Cloud Platform (GCP) project to get the client credentials
    1. You can follow [my note](https://cord-sodalite-2c6.notion.site/Google-Workspace-API-33864394338e4b3b90d63a1cbe754a2c) here is you are new to using Google Workplace API like me.

3. Create an integration w/ Notion and share the Notion DB you want to use w/ the tool w/ this integration.
    1. Follow https://developers.notion.com/docs/getting-started#step-1-create-an-integration

4. Run the app simply w/
```
python3 app.py -d <your_notion_db_id>
```

# Docker deployment
Recommend to run locally first to obtain Google access token.

1. Build the image w/
```
docker build -t google_cal_notion_sync .
```

2. Run the image w/
```
docker run -e NOTION_DB_ID=<your_notion_db_id> -d google_cal_notion_sync
```
