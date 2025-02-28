import VocabularyImporter from "@/components/VocabularyImporter";
import { Toaster } from "sonner";

export default function Home() {
  return (
    <main className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Vocabulary Language Importer</h1>
          <p className="text-muted-foreground mt-2">
            Generate structured vocabulary data based on thematic categories
          </p>
        </div>
        
        <VocabularyImporter />
        <Toaster position="top-center" />
      </div>
    </main>
  );
}