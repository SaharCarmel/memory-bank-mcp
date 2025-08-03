# React Todo App Example

This example shows MemBankBuilder's analysis of a modern React application with hooks, context, and testing.

## Source Code Structure

```
react-todo-app/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── TodoItem.jsx
│   │   ├── TodoList.jsx
│   │   └── AddTodo.jsx
│   ├── context/
│   │   └── TodoContext.jsx
│   ├── hooks/
│   │   └── useTodos.js
│   ├── utils/
│   │   └── storage.js
│   ├── App.jsx
│   ├── App.css
│   └── index.js
├── package.json
└── README.md
```

## Generated Memory Bank Analysis

When analyzed with:
```bash
uv run python -m memory_bank_core build react-todo-app --output-name todo-app-analysis
```

## Key Insights Generated

### Project Brief
- **Purpose**: Modern task management application built with React
- **Core Features**: Add, edit, delete, and persist todos
- **Architecture**: Component-based with Context API for state management
- **Testing Strategy**: Jest + React Testing Library

### System Patterns Identified
- **Component Pattern**: Functional components with React Hooks
- **Context Pattern**: Global state management via React Context
- **Custom Hooks**: Reusable logic extraction (useTodos)
- **Local Storage Pattern**: Data persistence without backend
- **Controlled Components**: Form handling with React patterns

### Technology Context
- **Framework**: React 18+ with functional components
- **State Management**: React Context API + useReducer
- **Styling**: CSS Modules + styled-components
- **Testing**: Jest, React Testing Library
- **Build Tool**: Create React App / Vite
- **Browser Support**: Modern browsers (ES6+)

### Architecture Analysis
```
Frontend Architecture:
├── App (Root Component)
├── TodoContext (State Provider)
├── TodoList (Container Component)
├── TodoItem (Presentational Component)
└── AddTodo (Form Component)

Data Flow:
User Input → Component → Context → Storage → Re-render
```

### Active Context Insights
- **Current State**: Feature-complete MVP
- **Recent Changes**: Added drag-and-drop functionality
- **Active Development**: Performance optimization
- **Next Features**: Categories, due dates, search

### Progress Status
- ✅ Core CRUD operations
- ✅ Local storage persistence  
- ✅ Responsive design
- ✅ Basic testing suite
- 🔄 Performance optimization
- ⏳ Advanced filtering
- ⏳ Multi-user support

## Sample Generated Files

### systemPatterns.md
```markdown
# React Todo App - System Patterns

## Architecture Classification
**Component-Based SPA** with unidirectional data flow

## Core Patterns

### 1. React Hooks Pattern
- useState for local component state
- useEffect for side effects
- useContext for global state access
- Custom hooks for reusable logic

### 2. Context + Reducer Pattern
```javascript
const TodoContext = React.createContext();
const todoReducer = (state, action) => { /* ... */ };
```

### 3. Controlled Components
- Form inputs controlled by React state
- Single source of truth for form data
- Predictable state updates

### 4. Composition Pattern
- Components composed of smaller components
- Props drilling avoided via Context
- Separation of concerns maintained
```

This example demonstrates how MemBankBuilder understands:
- Modern React patterns and best practices
- Component relationships and data flow
- Development status and next steps
- Architecture decisions and trade-offs

Perfect for:
- Team member onboarding
- Architecture documentation
- Code review preparation
- Project handovers