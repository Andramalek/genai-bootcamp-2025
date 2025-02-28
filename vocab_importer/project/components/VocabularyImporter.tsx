"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Loader2, Copy, Check, RefreshCw, AlertCircle, Info } from "lucide-react";
import { toast } from "sonner";

export default function VocabularyImporter() {
  const [theme, setTheme] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [vocabularyData, setVocabularyData] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [hasPlaceholders, setHasPlaceholders] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!theme.trim()) {
      toast.error("Please enter a theme");
      return;
    }

    setIsLoading(true);
    setVocabularyData("");
    setError(null);
    setHasPlaceholders(false);
    setMessage(null);
    
    try {
      const response = await fetch("/api/generate-vocabulary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ theme, retryCount }),
      });

      // Get the response as text first
      const responseText = await response.text();
      
      // Then try to parse it as JSON
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error("JSON Parse Error:", parseError);
        throw new Error(`Failed to parse response as JSON: ${responseText.substring(0, 100)}...`);
      }
      
      if (!response.ok) {
        throw new Error(data.error || "Failed to generate vocabulary");
      }

      if (!data.vocabulary || !Array.isArray(data.vocabulary)) {
        throw new Error("Invalid response format: Expected an array of vocabulary items");
      }

      // Check if we have at least one valid item
      if (data.vocabulary.length === 0) {
        throw new Error("No vocabulary items were generated. Please try again.");
      }

      // Check if any items have placeholder kanji (starts with '[' and ends with ']')
      const hasAnyPlaceholders = data.vocabulary.some(item => 
        typeof item.kanji === 'string' && 
        (
          (item.kanji.startsWith('[') && item.kanji.endsWith(']')) ||
          /^[a-zA-Z\s]+$/.test(item.kanji) || // English-only text
          item.kanji.includes('placeholder') ||
          item.kanji.includes('example')
        )
      );
      
      setHasPlaceholders(hasAnyPlaceholders);
      
      // Set any message from the API
      if (data.message) {
        setMessage(data.message);
      }
      
      const formattedData = JSON.stringify(data.vocabulary, null, 2);
      setVocabularyData(formattedData);
      
      if (hasAnyPlaceholders) {
        toast.info("Some vocabulary items have placeholder kanji. Try again for better results.");
      } else if (data.message) {
        toast.info(data.message);
      } else {
        toast.success("Vocabulary generated successfully!");
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred";
      setError(errorMessage);
      toast.error(errorMessage);
      console.error("Error generating vocabulary:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!vocabularyData) return;
    
    try {
      await navigator.clipboard.writeText(vocabularyData);
      setCopied(true);
      toast.success("Copied to clipboard!");
      
      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to copy to clipboard";
      toast.error(errorMessage);
    }
  };

  const retryGeneration = () => {
    if (theme.trim()) {
      setRetryCount(prev => prev + 1);
      handleSubmit(new Event('submit') as any);
    } else {
      toast.error("Please enter a theme before retrying");
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Vocabulary Language Importer</CardTitle>
          <CardDescription>
            Enter a thematic category to generate Japanese vocabulary items
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="theme">Theme</Label>
              <Input
                id="theme"
                placeholder="e.g., Food, Travel, Technology"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Enter a theme to generate vocabulary items in Japanese with romaji pronunciation and English translations.
              </p>
            </div>
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                "Generate Vocabulary"
              )}
            </Button>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-destructive/10 text-destructive rounded-md">
              <div className="flex items-start">
                <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-sm font-medium mb-1">Error occurred</h4>
                  <p className="text-sm">{error}</p>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={retryGeneration}
                  className="ml-2 flex-shrink-0"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              </div>
            </div>
          )}

          {message && (
            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-md">
              <div className="flex items-start">
                <Info className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5 text-blue-500" />
                <div className="flex-1">
                  <h4 className="text-sm font-medium mb-1 text-blue-700 dark:text-blue-400">Note</h4>
                  <p className="text-sm text-blue-600 dark:text-blue-300">
                    {message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {hasPlaceholders && vocabularyData && (
            <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-md">
              <div className="flex items-start">
                <Info className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5 text-amber-500" />
                <div className="flex-1">
                  <h4 className="text-sm font-medium mb-1 text-amber-700 dark:text-amber-400">Placeholder Kanji Detected</h4>
                  <p className="text-sm text-amber-600 dark:text-amber-300">
                    Some vocabulary items contain placeholder text (in square brackets) instead of actual kanji. 
                    Try generating again or using a different theme for better results.
                  </p>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={retryGeneration}
                  className="ml-2 flex-shrink-0 border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/30"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              </div>
            </div>
          )}

          {vocabularyData && (
            <div className="mt-6 space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="result">Generated Vocabulary</Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyToClipboard}
                  className="flex items-center gap-1"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
              <Textarea
                id="result"
                value={vocabularyData}
                readOnly
                className="font-mono h-96 overflow-auto"
              />
            </div>
          )}
        </CardContent>
        <CardFooter className="text-sm text-muted-foreground">
          The vocabulary is generated using Groq LLM based on your theme.
        </CardFooter>
      </Card>
    </div>
  );
}