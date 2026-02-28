# Node dependencies for AST analysis

The backend uses Node.js (Babel, Esprima, PostCSS) to analyze JavaScript/TypeScript and CSS files. Install dependencies here so the Python server can find them:

```bash
cd server/node_ast
npm install
```

If this directory has no `node_modules`, the server will still run but AST-based checks may log "Cannot find module" and fall back to other analysis (e.g. LLM).
