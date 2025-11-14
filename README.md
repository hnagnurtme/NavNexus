<p align="center" style="display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 15px;">
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/react/react-original.svg" height="55" title="React" />
  <img src="https://upload.wikimedia.org/wikipedia/commons/e/ee/.NET_Core_Logo.svg" height="55" title="ASP.NET Core" />
  <img src="https://papago.naver.com/static/img/papago_og.png" height="55" style="border-radius:10px;" title="Papago API" />
  <img src="https://ssl.pstatic.net/static/clovax/open-graph/og.png" height="55" style="border-radius:10px;" title="HyperCLOVA" />
  <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/Neo4j-logo_color.png" height="55" title="Neo4j" />
  <img src="https://media.blog.wisen.co.kr/wp-content/uploads/2017/12/11115340/ncp-2.png" height="55" title="Naver Cloud" />
  <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR2EGgiYPL-lhYXGy8f3x5_H7Bl6D-uvGg9Vm0DVK6853Ldw9geSjuHOAyDjjYtfYp5EQg&usqp=CAU" height="50" style="background:white; padding:5px; border-radius:10px;" title="Qdrant" />
</p>

# NavNexus — Multilingual Knowledge Graph Navigator

**NavNexus** is an AI-driven platform that transforms scattered, multilingual research documents into a living, interactive Knowledge Graph — turning static mindmaps into an immersive Knowledge Journey.

> Developed by **TheElite** for the
>
> <h4 align="center">
>   <a href="https://event.navercorp.vn/event/naver-vietnam-ai-hackathon-2025/" target="_blank">
>     Naver Vietnam AI Hackathon 2025
>   </a>
> </h4>

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/hnagnurtme/NavNexus.git
cd NavNexus

# Start all services with Docker Compose
docker compose up --build
```
---

## Key Features

- **Integrity Engine** – Harmonizes multilingual research terms into unified entities
using **HyperCLOVA X**, ensuring semantic consistency and accuracy across languages.

- **Discovery Map** – Visualizes the evolving Knowledge Graph built on Neo4j,
allowing users to explore relationships, patterns, and knowledge “crossroads.”

- **Inference Engine** – Enables **semantic queries** in natural language and  
  returns results through logical reasoning over the graph.

- **Recommendation Assistant** – Detects knowledge gaps (“orphan nodes”, “broken bridges”)  
  and proactively suggests multilingual search keywords for further exploration.

---

## Technology Stack

### Backend

- ASP.NET Core 8 Web API
- MediatR (CQRS)
- FluentValidation
- Neo4j.Driver
- Qdrant Client
- HyperCLOVA X API
- Papago Translation API
- Naver Object Storage (NOS) SDK

### Frontend

- React 18 + TypeScript
- Vite 5
- TailwindCSS 3

### Database

- Neo4j 5.18 Graph Database
- Qdrant Vector Database

---


## Documentation

- [Setup Guide](./SETUP.md) - Complete installation and configuration
- [Backend Documentation](./Backend/README.md) - API details and architecture
- [Frontend Documentation](./Frontend/README.md) - UI components and structure
---

## Team

Built with ❤️ by **NavNexus Hackathon Team**

**Questions?** Open an issue or check our [documentation](./SETUP.md).
