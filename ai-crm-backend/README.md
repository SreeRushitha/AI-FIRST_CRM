# AI First CRM

## Tech Stack

- React
- FastAPI
- PostgreSQL
- SQLAlchemy
- Groq LLM

## Features

- AI assisted HCP interaction
- Get interaction by ID
- PostgreSQL storage

## LangGraph Agent Tools

The AI First CRM uses LangGraph to route user requests to specialized AI tools.

### Available Tools

1. **Log Interaction**
   - Extracts structured interaction details from natural language and stores them in PostgreSQL.

2. **Follow-up Recommendation**
   - Suggests practical follow-up actions after an HCP interaction.

3. **Product Recommendation**
   - Recommends relevant pharmaceutical products, brochures, clinical materials, and samples.

4. **Sentiment Analysis**
   - Analyzes the overall sentiment of the interaction and provides a short explanation.

5. **Interaction Summary**
   - Generates a concise summary of the healthcare professional interaction.

6. **Doctor Insights**
   - Identifies the doctor's specialization, interests, and concerns from the conversation.

7. **Meeting Preparation**
   - Suggests how the medical representative should prepare for the next meeting.
## Run Backend

pip install -r requirements.txt
uvicorn app:app --reload

## Run Frontend

npm install
npm run dev

