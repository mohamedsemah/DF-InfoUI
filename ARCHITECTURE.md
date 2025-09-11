# DF-InfoUI Architecture

## Agent Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        BRAIN AGENT                              │
│                    (Supervisor/Planner)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ 1. Receives uploaded code files
                      │ 2. Scans and detects accessibility issues
                      │ 3. Classifies issues into POUR categories
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ISSUE CLASSIFICATION                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  │ Perceivable │  │  Operable   │  │Understandable│  │   Robust    │
│  │   Issues    │  │   Issues    │  │   Issues     │  │   Issues    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ 4. Sends each group to corresponding neuron
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4 POUR NEURON AGENTS                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  │ Perceivable │  │  Operable   │  │Understandable│  │   Robust    │
│  │   Agent     │  │   Agent     │  │    Agent     │  │   Agent     │
│  │             │  │             │  │              │  │             │
│  │ • Alt text  │  │ • Labels    │  │ • Headings   │  │ • ARIA roles│
│  │ • Contrast  │  │ • ARIA      │  │ • Forms      │  │ • HTML valid│
│  │ • Text alt  │  │ • Keyboard  │  │ • Errors     │  │ • Semantic  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ 5. Each neuron generates fixes and reports
                      │    (before/after code snippets)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NEURON REPORTS                               │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  │ Perceivable │  │  Operable   │  │Understandable│  │   Robust    │
│  │   Report    │  │   Report    │  │   Report     │  │   Report    │
│  │             │  │             │  │              │  │             │
│  │ • Fixes     │  │ • Fixes     │  │ • Fixes      │  │ • Fixes     │
│  │ • Before    │  │ • Before    │  │ • Before     │  │ • Before    │
│  │ • After     │  │ • After     │  │ • After      │  │ • After     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ 6. Brain Agent receives 4 reports
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BRAIN AGENT                                  │
│                    (Implementation)                             │
│                                                                 │
│ 7. Implements the changes in code files                        │
│ 8. Validates fixes using ESLint + axe-core                     │
│ 9. Generates fixed ZIP file                                    │
│ 10. Creates user-friendly PDF report                           │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Steps

1. **Upload**: User uploads ZIP file
2. **Brain Agent Analysis**: Scans files, detects issues, classifies into POUR
3. **Neuron Processing**: Each POUR agent fixes their category of issues
4. **Report Generation**: Each neuron returns before/after code snippets
5. **Brain Agent Implementation**: Applies fixes, validates, generates artifacts
6. **Delivery**: Returns fixed ZIP + PDF report

## Key Features

- **Brain Agent**: Single supervisor coordinating the entire process
- **4 POUR Neurons**: Specialized agents for each accessibility category
- **Clear Separation**: Detection vs. Fixing vs. Implementation
- **Comprehensive Reports**: Before/after code snippets from each neuron
- **Validation**: ESLint + axe-core validation of all fixes
- **User-Friendly Output**: Fixed code + detailed PDF report
