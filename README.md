# Navigate413

## Inspiration
The concept for **Navigate413** was born from a common struggle: the overwhelming density of university-related documents like financial aid letters, housing leases, and institutional notices. These documents are often written in complex legal or institutional language that is difficult for students to interpret accurately. This barrier frequently leads to missed deadlines, misunderstood obligations, and significant stress. 

This problem particularly affects **international and first-generation students** who may be encountering these specific bureaucratic structures for the first time. Our mission was to build a tool that does more than just summarize; we created a bridge that transforms static, confusing text into clear, actionable guidance.

---

## What it does
Navigate413 converts complex institutional documents into structured insights to help students make informed decisions. Unlike a standard chatbot, it analyzes the specific consequences of a document, offering **quantitative risk analysis** and **cause-effect modeling**.

- **Identifies Risks and Obligations:** The system flags potential pitfalls and explains what the student is legally or financially bound to do.
- **Simulates Scenarios:** Through a specialized **Scenario Agent**, students can explore "what-if" decisions, such as the estimated cost of breaking a lease early.
- **Real-time Translation:** The application provides accurate contextual translation in a single click, supporting students who are not native English speakers.
- **Campus Connectivity:** It connects students to real campus help, such as the bursar or financial aid office.

---

## How we built it
The architecture of Navigate413 is centered around a **Multi-Agent Coordination** system powered by **LangGraph**, which orchestrates specialized agents to ensure high-quality, domain-specific outputs.

### Advanced Document Parsing
To ensure accuracy, our document pipeline uses a **Hybrid PDF Parser**:

- **OCR and Text-Based Extraction:** The system utilizes both Optical Character Recognition for scanned images and standard text extraction for digital PDFs.
- **NLTK Integration:** We leverage the Natural Language Toolkit for precise tokenization and segmentation of dense institutional text.
- **Retrieval-Augmented Generation (RAG):** This allows our agents to perform semantic retrieval, ensuring they pull the most relevant context from the document before generating an analysis.

### Technical Stack

- **Gemini API**
  - Serves as the core reasoning engine for complex document interpretation.
  - Generates high-dimensional **embeddings** for the RAG pipeline.
  - Powers the logic behind simulating "what-if" outcomes.

- **MongoDB Atlas**
  - Operates as our primary **Vector Database** for semantic retrieval.
  - Manages the storage of document segments and metadata.
  - Provides a scalable cloud environment for distributed data management.

- **DigitalOcean**
  - Acts as the primary **hosting** provider for the entire application.
  - Supports the **FastAPI** backend for high-performance processing.
  - Hosts the **React and Tailwind** frontend dashboard.

---

## Flowchart

```text
                               +----------------------+
                               |    UMass Student     |
                               +-----------+----------+
                                           | (Upload PDF)
                                           v
+------------------------------------------------------------------------+
|                            Backend Service                             |
|                         [ Hybrid Parsing Flow ]                        |
|   1. OCR + Text Extraction -> 2. NLTK Segmentation -> 3. Gemini Embed  |
+------------------------------------+-----------------------------------+
                                     | (Text & Embeddings)
                                     v
                           +-------------------------+
                           |  MongoDB Atlas Platform | 
                           | [DocStore & Vector Index]|
                           +-------------------------+
                                     ^
                                     | (Semantic Retrieval)
                                     |
+------------------------------------+-----------------------------------+
|                            Backend Service                             |
|                       [ LangGraph Agent Swarm ]                        |
|    1. Intent Router -> 2. Specialist Agents (Finance, Housing, etc.)   |
|    3. RAG Resource Agent -> 4. Translation Agent                       |
+------------------+-----------------+-----------------------------------+
                   | (Specialist Data) | (Risk & Scenario Analysis)
                   v                   v
         +------------------+      +------------------+
         |  Gemini 1.5 API  |      |   DigitalOcean   |
         | (Reasoning/Logic)|      | (App Deployment) |
         +--------+---------+      +---------+--------+
                  |                          |
                  +------------+-------------+
                               | (Structured JSON)
                               v
                       +-----------------------+
                       |    React Dashboard    |
                       | (Interactive Insights)|
                       +-----------------------+
```

---

## Challenges we ran into

Building a distributed, agent-based system presented several infrastructure hurdles:

- **Network Connectivity:** We faced difficulties configuring **MongoDB Atlas** in its own cluster while allowing a specific IP from **DigitalOcean** to connect. This caused persistent network issues across distributed cluster nodes.
- **Vector Search Complexity:** Implementing and optimizing **Vector Search** on MongoDB Atlas required significant effort to ensure the RAG pipeline was both fast and accurate.
- **Infrastructure Routing:** We encountered **routing issues** on DigitalOcean between the IP and specific configuration permissions, leading to deployment delays.
- **Institutional Nuance:** Ensuring the AI focused on specific university workflows rather than general knowledge required careful prompt engineering and agent tuning.

---

## Accomplishments that we're proud of

We are proud to have built a system that is **not just a ChatGPT wrapper**. By using multiple orchestrated specialized agents, we provide **quantitative analysis**—such as calculating the financial risk of a delayed payment—rather than just a generic summary. We successfully transformed static, intimidating documents into interactive tools that empower students to act with confidence.

---

## What we learned

We learned that the gap between university resources and student understanding is often a matter of language and accessibility. We also discovered that effective AI orchestration requires a deep integration of specialized tools—like combining **NLTK** for parsing with **LangGraph** for stateful logic—to handle the nuances of institutional documentation.

---

## What's next for Navigate413

Looking ahead, we plan to:

- **Expand** the platform to other universities beyond UMass.
- **Enhance Accessibility** by adding support for more languages and mobile-specific features.
- **Institutional Integration**, allowing universities to adopt Navigate413 as a native support platform for their student body.
