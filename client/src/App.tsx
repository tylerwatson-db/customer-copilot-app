import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { QueryInterface } from "./components/QueryInterface";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <QueryInterface />
    </QueryClientProvider>
  );
}

export default App;
